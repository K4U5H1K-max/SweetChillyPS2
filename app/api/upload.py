from fastapi import APIRouter, HTTPException
from fastapi import UploadFile
from fastapi import File
from app.services.file_service import save_file
from app.pipelines.document_pipeline import DocumentPipeline
router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Only PDF, JPEG, and PNG files are allowed."
        )

    saved_path = await save_file(file)

    pipeline = DocumentPipeline()
    result = await pipeline.process(saved_path)

    return {
        "message": "File uploaded successfully",
        "original_filename": file.filename,
        "saved_path": str(saved_path),
        "pipeline": result
    }

