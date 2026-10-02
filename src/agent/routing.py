from typing import Literal

from .graph_state import State


def routing_fn(state: State) -> Literal["csv", "database"]:
    if state.get("db_url"):
        return "database"
    if state.get("csv_url"):
        return "csv"
    raise ValueError("Agent state must include csv_url or db_url")
