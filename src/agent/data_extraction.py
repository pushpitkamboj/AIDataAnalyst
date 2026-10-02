import pandas as pd
from langchain_core.messages import AIMessage

from utils.database import extract_schema_context
from utils.logging import get_logger

from .graph_state import State

logger = get_logger(__name__)


def extract_db_info(state: State):
    """Extract database schema metadata using SQLAlchemy."""
    url = state.get("db_url")
    logger.info("Extracting database metadata")

    try:
        schema_context, dialect = extract_schema_context(url)
    except Exception as exc:
        logger.exception("Error extracting database schema")
        schema_context = {"error": str(exc)}
        dialect = "unknown"

    response = AIMessage(
        content="all the relevant metadata about database has been generated and stored in the state",
    )
    
    return {
        "schema_context": schema_context,
        "messages": [response],
        "dialect": dialect
    }


def csv_metadata(file_url: str) -> dict:
    df = pd.read_csv(file_url)

    meta = {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
        "head": df.head(5).to_dict(orient="records"),
    }
    return meta


def extract_csv_info(state: State):
    public_url = state.get("csv_url")
    data = csv_metadata(public_url)
    
    response = AIMessage(
        content="all the relevant metadata about the csv file has been generated and stored in the state",
    )
    
    return {
        "messages": [response],
        "schema_context": data,
        "dialect": "sqlite", #because the docs of DuckDB say they mimic exactly the sqlite
    }
