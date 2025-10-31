#decide the info is csv or connection string, accordingly save them in state and cloud, return the cloud link
from dotenv import load_dotenv
load_dotenv()

from .graph_state import State
from langgraph.graph import START
from typing_extensions import TypedDict

def routing_fn(state: State):
    if state.get("db_url"):
        return "database"
    if state.get("csv_url"):
        return "csv"


