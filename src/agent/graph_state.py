from dotenv import load_dotenv
load_dotenv()

from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from e2b_code_interpreter import Sandbox
import pandas as pd
from typing import List, Dict, Any


class State(TypedDict):
    messages: Annotated[list, add_messages]
    schema_context: dict[str]
    db_url: str
    csv_url: str
    sandbox_id: str
    dialect: str
    query: str
    sql_query_output: List[Dict[str, Any]]
    python_code: str
    result: str
    image_urls: list[str]
    decision: str
    
    code_status: bool
    code_error: List[Any]
    