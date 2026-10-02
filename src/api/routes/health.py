from fastapi import APIRouter

from api.schemas import MessageResponse

router = APIRouter()


@router.get("/health", response_model=MessageResponse)
def health() -> MessageResponse:
    return MessageResponse(message="health is ok")
