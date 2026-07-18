import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File as FastAPIFile, Form, HTTPException, UploadFile

from pydantic import BaseModel

from src.core.files import get_files
from src.core.settings import settings
from src.schemas.files import File, Folder

router = APIRouter()


class PaginatedResponse(BaseModel):
    count: int
    results: List[File | Folder]


@router.get("/files", tags=["files"])
async def list_files() -> PaginatedResponse:
    files = get_files(relative_path=None)

    return PaginatedResponse(count=len(files), results=files)


def save_file(path: str, upload_file: UploadFile) -> Path:
    working_dir = Path(settings.working_dir)

    file_path = (working_dir / path).resolve()

    if not file_path.is_relative_to(working_dir):
        raise HTTPException(status_code=400, detail="Invalid path.")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

    return file_path


@router.post("/files/upload", response_model=File, tags=["files"])
async def upload_file(
    file: UploadFile = FastAPIFile(...),
) -> File:
    destination_path = file.filename

    saved_path = save_file(destination_path, file)

    return File(
        name=saved_path.name,
        path=Path(destination_path),
    )
