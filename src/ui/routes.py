from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, File as FastAPIFile, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from src.core.files import get_files, delete_file_or_folder
from src.core.settings import settings
from src.i18n import init_translations, resolve_locale, set_locale
from src.i18n.extensions import I18nExtension

router = APIRouter(prefix="/ui")

templates = Jinja2Templates(directory="src/ui/templates")
templates.env.add_extension(I18nExtension)
init_translations()


@router.get("", response_class=HTMLResponse, tags=["ui"])
async def index(request: Request):
    locale = resolve_locale(request)
    set_locale(locale)
    files = get_files(relative_path=None)
    return templates.TemplateResponse(
        request=request, name="index.html", context={"files": files, "locale": locale}
    )


@router.get(
    "/files/view/{relative_path:path}", response_class=HTMLResponse, tags=["ui/files"]
)
async def view_files(request: Request, relative_path: str = "."):
    locale = resolve_locale(request)
    set_locale(locale)
    files = get_files(Path(relative_path))

    return templates.TemplateResponse(
        request=request, name="index.html", context={"files": files, "locale": locale}
    )


def get_file(path: str) -> Path:
    working_dir = Path(settings.working_dir)

    file_path = (working_dir / path).resolve()

    if not file_path.is_relative_to(working_dir):
        raise HTTPException(status_code=400, detail="Invalid path.")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    return file_path


@router.get(
    "/files/delete/{file_path:path}", response_class=FileResponse, tags=["ui/files"]
)
async def delete_file(file_path: str) -> RedirectResponse:
    file_path = Path(file_path)
    if not file_path.exists():
        return RedirectResponse("/ui")

    working_dir = Path(settings.working_dir)

    delete_file_or_folder(file_path)

    if not file_path.is_relative_to(working_dir):
        raise HTTPException(status_code=400, detail="Invalid path.")

    return RedirectResponse("/ui")


@router.get(
    "/files/download/{file_path:path}", response_class=FileResponse, tags=["ui/files"]
)
async def download_file(file_path: str) -> FileResponse:
    file_path = get_file(file_path)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.post("/files/upload", tags=["ui/files"])
async def upload_file(
    file: UploadFile = FastAPIFile(...),
) -> RedirectResponse:
    working_dir = Path(settings.working_dir)
    destination = working_dir / file.filename

    with destination.open("wb") as out:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            out.write(chunk)

    await file.close()

    return RedirectResponse("/ui", status_code=303)
