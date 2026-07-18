import logging
import shutil

from pathlib import Path
from typing import Optional, List

from src.core.settings import settings
from src.schemas.files import Folder, File

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_files(relative_path: Optional[Path]) -> List:
    if not relative_path:
        working_dir = Path(settings.working_dir)
    else:
        working_dir = Path(settings.working_dir) / Path(relative_path)

    logger.info("Getting files for %s", working_dir)

    files = []
    if not working_dir.is_dir():
        logger.warning("The specified working directory is not a directory.")
        return files

    for x in working_dir.iterdir():
        resolved_path = x.resolve()

        if x.is_dir():
            f = Folder(name=x.name, path=Path(resolved_path))
        else:
            f = File(name=x.name, path=Path(resolved_path))
        files.append(f)

    return files


def delete_file_or_folder(file_path: Path):
    if file_path.is_file():
        Path.unlink(file_path)
    else:
        shutil.rmtree(file_path)
