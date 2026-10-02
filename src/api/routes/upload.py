from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from api.schemas import MessageResponse
from utils.errors import bad_request, run_route
from utils.settings import get_settings
from utils.storage import upload_bytes

router = APIRouter()


@router.post("/upload", response_model=MessageResponse)
async def upload_data(
    file: UploadFile | None = File(None),
    db_url: str | None = Form(None),
) -> MessageResponse:
    async def handler() -> MessageResponse:
        if file and db_url:
            bad_request("Upload either a CSV file or a database URL, not both")
        if db_url:
            return MessageResponse(message=db_url)
        if not file:
            bad_request("Upload a CSV file or provide a database URL")
        public_url = await _upload_csv(file)
        return MessageResponse(message=public_url)
    return await run_route("upload_data", handler)


async def _upload_csv(file: UploadFile) -> str:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        bad_request("Only CSV files are allowed")
    contents = await file.read()
    if not contents:
        bad_request("Uploaded file is empty")
    extension = Path(file.filename).suffix or ".csv"
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{extension}"
    settings = get_settings()
    return upload_bytes(
        bucket_name=settings.csv_bucket_name,
        filename=filename,
        contents=contents,
        content_type="text/csv",
    )
