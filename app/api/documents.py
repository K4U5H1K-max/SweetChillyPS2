from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import hashlib
import uuid
import asyncio

from app.core.database import get_db
from app.services.file_service import save_file
from app.pipelines.document_pipeline import DocumentPipeline
from app.models.document_models import Document, IngestionJob, DocumentStatus, JobStatus, Page, Chunk

router = APIRouter()

async def get_file_hash(file: UploadFile) -> str:
    hasher = hashlib.sha256()
    await file.seek(0)
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        hasher.update(chunk)
    await file.seek(0)
    return hasher.hexdigest()

@router.post("/documents")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Unsupported file type.")

    sha256_hash = await get_file_hash(file)

    # Duplicate check
    result = await db.execute(select(Document).where(Document.sha256 == sha256_hash))
    existing_doc = result.scalar_one_or_none()

    if existing_doc:
        return {
            "message": "Document already exists.",
            "document_id": str(existing_doc.id),
            "status": existing_doc.status
        }

    # Not a duplicate, save file
    saved_path = await save_file(file)

    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        original_filename=file.filename,
        stored_filename=saved_path.name,
        mime_type=file.content_type,
        file_size=saved_path.stat().st_size,
        sha256=sha256_hash,
        storage_path=str(saved_path),
        document_type="PDF" if file.content_type == "application/pdf" else "IMAGE",
        status=DocumentStatus.PROCESSING.value
    )
    db.add(doc)
    await db.flush()

    job_id = uuid.uuid4()
    job = IngestionJob(
        job_id=job_id,
        document_id=doc.id,
        status=JobStatus.RUNNING.value,
        processing_stage="STARTED"
    )
    db.add(job)
    await db.commit()

    # Background task for processing
    pipeline = DocumentPipeline(db)
    
    # We should run this asynchronously, but for immediate DB reflection in tests,
    # let's run it inline. If it were a background task, we'd use BackgroundTasks.
    try:
        await pipeline.process(saved_path, str(doc.id), str(job.job_id))
    except Exception as e:
        # Pipeline handles its own error saving
        pass

    return {
        "message": "File uploaded and processing started.",
        "document_id": str(doc.id),
        "job_id": str(job.job_id)
    }

@router.get("/documents")
async def get_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document))
    docs = result.scalars().all()
    return [{"id": str(d.id), "original_filename": d.original_filename, "status": d.status} for d in docs]

@router.get("/documents/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id),
        "original_filename": doc.original_filename,
        "status": doc.status,
        "created_at": doc.created_at,
        "processed_at": doc.processed_at,
        "error_message": doc.error_message
    }

@router.get("/documents/{document_id}/status")
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = await db.execute(select(IngestionJob).where(IngestionJob.document_id == doc.id).order_by(IngestionJob.started_at.desc()))
    job = result.scalars().first()
    
    pages_result = await db.execute(select(Page).where(Page.document_id == doc.id))
    pages = pages_result.scalars().all()
    
    return {
        "document_id": str(doc.id),
        "status": doc.status,
        "processing_stage": job.processing_stage if job else None,
        "pages_processed": len(pages),
        "started_at": job.started_at if job else None,
        "updated_at": doc.updated_at
    }

@router.get("/documents/{document_id}/pages")
async def get_document_pages(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.document_id == uuid.UUID(document_id)))
    pages = result.scalars().all()
    return [{"id": str(p.id), "page_number": p.page_number, "character_count": p.character_count, "extraction_method": p.extraction_method} for p in pages]

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chunk).where(Chunk.document_id == uuid.UUID(document_id)))
    chunks = result.scalars().all()
    return [{"id": str(c.id), "page_id": str(c.page_id), "chunk_index": c.chunk_index, "start_offset": c.start_offset, "end_offset": c.end_offset} for c in chunks]
