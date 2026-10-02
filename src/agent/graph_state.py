from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list, add_messages]
    schema_context: dict[str, Any]
    db_url: str
    csv_url: str
    sandbox_id: str
    dialect: str
    query: str
    sql_query_output: list[dict[str, Any]]
    python_code: str
    result: str
    image_urls: list[str]
    decision: str
    
    code_status: bool
    code_error: str
    query_error: str
    retry_count: int
