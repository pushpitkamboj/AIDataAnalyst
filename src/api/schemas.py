from pydantic import BaseModel

class MessageResponse(BaseModel):
    message: str

class QueryRequest(BaseModel):
    query: str
    csv_url: str | None = None
    db_url: str | None = None
