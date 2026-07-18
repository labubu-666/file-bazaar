from pathlib import Path

from pydantic import BaseModel


class File(BaseModel):
    name: str
    path: Path
    type: str = "file"


class Folder(BaseModel):
    name: str
    path: Path
    type: str = "folder"
