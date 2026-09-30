import pytest
import pytest_asyncio
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.document_models import Base, Document, IngestionJob, Page, Chunk
from app.pipelines.document_pipeline import DocumentPipeline
import hashlib

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session

@pytest.mark.asyncio
async def test_document_ingestion_lifecycle(db_session: AsyncSession, tmp_path: Path):
    # Setup test file
    test_file = tmp_path / "test.pdf"
    test_file.write_text("dummy pdf content")
    
    # 1. Create Document and Job (simulating upload)
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    doc = Document(
        id=doc_id,
        original_filename="test.pdf",
        stored_filename="test_uuid.pdf",
        mime_type="application/pdf",
        file_size=1024,
        sha256=hashlib.sha256(b"dummy pdf content").hexdigest(),
        storage_path=str(test_file),
        document_type="PDF"
    )
    job = IngestionJob(
        job_id=job_id,
        document_id=doc.id,
        status="RUNNING",
        processing_stage="STARTED"
    )
    
    db_session.add(doc)
    db_session.add(job)
    await db_session.commit()
    
    # Verify persistence
    saved_doc = await db_session.get(Document, doc_id)
    assert saved_doc is not None
    assert saved_doc.status == "UPLOADED"
    
    # Mocking out the actual extraction/embedding services for DB lifecycle test
    class MockPipeline(DocumentPipeline):
        async def _process_pdf(self, file_path, doc, job):
            # Mock persistence logic
            job.processing_stage = "EXTRACTING_TEXT"
            await self.db.commit()
            
            page = Page(document_id=doc.id, page_number=1, text="mock text", extraction_method="TEXT_EXTRACTION", character_count=9)
            self.db.add(page)
            await self.db.flush()
            
            chunk = Chunk(document_id=doc.id, page_id=page.id, chunk_index=0, text="mock text", start_offset=0, end_offset=9, qdrant_point_id="mock_id")
            self.db.add(chunk)
            await self.db.commit()
            
            return {"pages": 1, "chunks": 1}

    pipeline = MockPipeline(db_session)
    await pipeline.process(test_file, str(doc_id), str(job_id))
    
    # Verify final states
    await db_session.refresh(saved_doc)
    await db_session.refresh(job)
    
    assert saved_doc.status == "PROCESSED"
    assert job.status == "COMPLETED"
    assert job.processing_stage == "COMPLETED"
    
    # Verify pages and chunks
    from sqlalchemy import select
    pages = (await db_session.execute(select(Page).where(Page.document_id == doc_id))).scalars().all()
    assert len(pages) == 1
    
    chunks = (await db_session.execute(select(Chunk).where(Chunk.document_id == doc_id))).scalars().all()
    assert len(chunks) == 1
    assert chunks[0].page_id == pages[0].id
