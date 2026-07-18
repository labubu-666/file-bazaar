import logging
import os
import sys
from os import PathLike
from pathlib import Path

import click
import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.routers.files import router as files_router
from src.core.settings import settings
from src.ui.routes import router as ui_router

logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


app = FastAPI(debug=True, docs_url="/api/v1/docs", title="file-bazaar", version="0.0.0")

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(files_router)

app.include_router(api_router)

app.include_router(ui_router)


@app.get("/", response_class=HTMLResponse)
def redirect_to_ui():
    return RedirectResponse("/ui")


@cli.command()
@click.option("--working-dir", default=".", help="Working dir.")
def serve(working_dir: PathLike):
    working_dir_path = Path(working_dir)
    if not working_dir_path.exists():
        sys.exit("Specified working dir does not exist.")

    os.environ["FILE_BAZAAR_WORKING_DIR"] = str(working_dir_path.resolve())

    settings.working_dir = working_dir_path

    uvicorn.run("main:app", host="0.0.0.0", port=7189, reload=True)


if __name__ == "__main__":
    cli()
