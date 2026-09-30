from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_file(file: UploadFile) -> Path:
    """
    Save uploaded file to disk and return its path.
    """

    # Get original extension (.pdf, .png, ...)
    extension = Path(file.filename).suffix

    # Generate unique filename
    filename = f"{uuid4()}{extension}" #Universally Unique Identifier

    # Final path
    file_path = UPLOAD_DIR / filename

    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return file_path
