from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import health, query, upload
from utils.logging import configure_logging
from utils.settings import get_settings


def create_app() -> FastAPI:
    get_settings().apply_to_environment()
    configure_logging()

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(query.router)
    mount_frontend(app)
    return app


def mount_frontend(app: FastAPI) -> None:
    frontend_dir = Path(__file__).resolve().parents[1] / "ui" / "fe"
    if not frontend_dir.exists():
        return

    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    @app.get("/chat.html", include_in_schema=False)
    def chat() -> FileResponse:
        return FileResponse(frontend_dir / "chat.html")


app = create_app()
