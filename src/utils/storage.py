from typing import Any

from supabase import Client, create_client

from .errors import server_error
from .settings import get_settings


def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        server_error("Supabase credentials are not configured")
    return create_client(settings.supabase_url, settings.supabase_key)


def _extract_uploaded_path(response: Any) -> str:
    if isinstance(response, dict):
        if response.get("error"):
            server_error(f"Supabase error: {response['error']}")
        data = response.get("data") or response.get("Data") or {}
        path = data.get("path") if isinstance(data, dict) else data
        path = path or response.get("path") or response.get("Key")
    else:
        path = getattr(response, "path", None) or getattr(response, "key", None)

    if not path:
        server_error(f"Upload succeeded but Supabase did not return a path: {response}")
    return str(path)


def _extract_public_url(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        url = (
            response.get("publicUrl")
            or response.get("publicURL")
            or response.get("public_url")
            or response.get("public")
        )
    else:
        url = (
            getattr(response, "publicUrl", None)
            or getattr(response, "publicURL", None)
            or getattr(response, "public_url", None)
        )

    if not url:
        server_error(f"Could not derive public URL from Supabase response: {response}")
    return str(url)


def upload_bytes(
    *,
    bucket_name: str,
    filename: str,
    contents: bytes,
    content_type: str,
) -> str:
    client = get_supabase_client()
    bucket = client.storage.from_(bucket_name)
    response = bucket.upload(filename, contents, {"content-type": content_type})
    path = _extract_uploaded_path(response)
    return _extract_public_url(bucket.get_public_url(path))
