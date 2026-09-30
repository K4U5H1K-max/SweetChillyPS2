import os
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document_models import Document, IngestionJob, Page, Chunk, DocumentStatus, JobStatus
from app.services.pdf_service import extract_text_from_pdf
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import OCRService
from app.services.text_cleaner import TextCleaner
from app.services.chunking_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


class DocumentPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cleaner = TextCleaner()
        self.classifier = DocumentClassifier()
        self.ocr_service = OCRService()
        self.chunk_service = ChunkService()
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.qdrant_service.create_collection()

    async def process(self, file_path: Path, document_id: str, job_id: str):
        print(f"Processing file: {file_path}")
        
        # Get job and document
        import uuid
        job = await self.db.get(IngestionJob, uuid.UUID(job_id) if isinstance(job_id, str) else job_id)
        doc = await self.db.get(Document, uuid.UUID(document_id) if isinstance(document_id, str) else document_id)
        
        if not job or not doc:
            raise ValueError("Invalid document or job ID")

        try:
            job.processing_stage = "VALIDATING_FILE"
            await self.db.commit()

            extension = file_path.suffix.lower()
            print(f"Detected file type: {extension}")
            
            if extension == ".pdf":
                result = await self._process_pdf(file_path, doc, job)
            elif extension in [".png", ".jpg", ".jpeg"]:
                result = await self._process_image(file_path, doc, job)
            else:
                raise ValueError(f"Unsupported file type: {extension}")
            
            # Mark Success
            job.status = JobStatus.COMPLETED.value
            job.completed_at = datetime.now(timezone.utc)
            job.processing_stage = "COMPLETED"
            
            doc.status = DocumentStatus.PROCESSED.value
            doc.processed_at = datetime.now(timezone.utc)
            await self.db.commit()
            
            return result

        except Exception as e:
            # Mark Failure
            job.status = JobStatus.FAILED.value
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            
            doc.status = DocumentStatus.FAILED.value
            doc.error_message = str(e)
            await self.db.commit()
            print(f"Pipeline failed: {e}")
            raise e

    async def _process_pdf(self, file_path: Path, doc: Document, job: IngestionJob):
        job.processing_stage = "EXTRACTING_TEXT"
        await self.db.commit()

        document = extract_text_from_pdf(file_path)
        for page in document.page_data:
            page.text = self.cleaner.clean(page.text)
        document.text = "\n".join(page.text for page in document.page_data)

        job.processing_stage = "CLASSIFYING_DOCUMENT"
        await self.db.commit()
        
        document.characters = len(document.text)
        document.is_empty = len(document.text.strip()) == 0
        decision = self.classifier.classify(document)
        extraction_method = "TEXT_EXTRACTION"

        if decision == "ocr":
            job.processing_stage = "RUNNING_OCR"
            await self.db.commit()
            document = self.ocr_service.extract_text(file_path)
            for page in document.page_data:
                page.text = self.cleaner.clean(page.text)
            document.text = "\n".join(page.text for page in document.page_data)
            document.characters = len(document.text)
            document.is_empty = len(document.text.strip()) == 0
            extraction_method = "OCR"

        return await self._persist_and_index(document, doc, job, extraction_method)

    async def _process_image(self, file_path: Path, doc: Document, job: IngestionJob):
        job.processing_stage = "RUNNING_OCR"
        await self.db.commit()

        document = self.ocr_service.extract_text(file_path)
        for page in document.page_data:
            page.text = self.cleaner.clean(page.text)
        document.text = "\n".join(page.text for page in document.page_data)
        document.characters = len(document.text)
        document.is_empty = len(document.text.strip()) == 0
        
        return await self._persist_and_index(document, doc, job, "OCR")

    async def _persist_and_index(self, document_dto, doc: Document, job: IngestionJob, extraction_method: str):
        job.processing_stage = "PERSISTING_PAGES"
        await self.db.commit()

        pages = []
        for i, p_data in enumerate(document_dto.page_data):
            page_obj = Page(
                document_id=doc.id,
                page_number=p_data.page,
                text=p_data.text,
                extraction_method=extraction_method,
                character_count=len(p_data.text)
            )
            self.db.add(page_obj)
            pages.append(page_obj)
        
        await self.db.flush() # flush to get page IDs

        job.processing_stage = "CREATING_CHUNKS"
        await self.db.commit()

        chunks = self.chunk_service.split(
            pages=document_dto.page_data,
            source=document_dto.source
        )

        job.processing_stage = "INDEXING_QDRANT"
        await self.db.commit()
        
        embeddings = self.embedding_service.encode(chunks)
        
        db_chunks = []
        qdrant_points = []
        import uuid
        
        for i, chunk_dto in enumerate(chunks):
            chunk_id = uuid.uuid4()
            page_id = next(p.id for p in pages if p.page_number == chunk_dto.page)
            
            chunk_obj = Chunk(
                id=chunk_id,
                document_id=doc.id,
                page_id=page_id,
                chunk_index=i,
                text=chunk_dto.text,
                start_offset=0, # If no actual offset available
                end_offset=len(chunk_dto.text),
                qdrant_point_id=str(chunk_id) # Using same ID for Qdrant point
            )
            self.db.add(chunk_obj)
            db_chunks.append(chunk_obj)
            
            # Map for Qdrant storage
            qdrant_points.append({
                "id": str(chunk_id),
                "embedding": embeddings[i].embedding,
                "payload": {
                    "document_id": str(doc.id),
                    "page_id": str(page_id),
                    "chunk_id": str(chunk_id),
                    "page_number": chunk_dto.page,
                    "chunk_index": i,
                    "text": chunk_dto.text,
                    "source": chunk_dto.source,
                }
            })
            
        await self.db.flush()
        
        # Store in Qdrant via custom method
        self.qdrant_service.store_points(qdrant_points)
        
        return {
            "pages": len(pages),
            "chunks": len(db_chunks)
        }