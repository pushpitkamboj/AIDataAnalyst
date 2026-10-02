import base64
import datetime

import duckdb
from e2b_code_interpreter import Sandbox
from langchain_core.messages import AIMessage

from utils.database import read_query
from utils.errors import agent_retry_error
from utils.settings import get_settings
from utils.storage import upload_bytes

from .graph_state import State

settings = get_settings()
settings.apply_to_environment()


def run_query(state: State):
    """Execute SQL query on CSV or DB and return rows."""
    query = state.get("query")

    try:
        if state.get("csv_url"):
            with duckdb.connect() as connection:
                df = connection.execute(query).df()
        elif state.get("db_url"):
            df = read_query(state["db_url"], query)
        else:
            raise ValueError("Missing csv_url or db_url")
    except Exception as exc:
        return agent_retry_error(exc, state, error_key="query_error")

    return {
        "sql_query_output": df.to_dict(orient="records"),
        "query_error": None,
    }


def run_code(state: State):
    sbx = Sandbox.connect(state["sandbox_id"])

    try:
        execution = sbx.run_code(state["python_code"])

        if execution.error:
            return {
                "code_error": str(execution.error),
                "code_status": False,
                "retry_count": state.get("retry_count", 0) + 1,
            }

        public_urls = []
        for result_idx, result in enumerate(result for result in execution.results if result.png):
            img_bytes = base64.b64decode(result.png)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"chart-{result_idx}-{timestamp}.png"
            public_urls.append(
                upload_bytes(
                    bucket_name=settings.image_bucket_name,
                    filename=filename,
                    contents=img_bytes,
                    content_type="image/png",
                )
            )

        sbx.kill()
        return {
            "messages": [
                AIMessage(content=f"Code executed successfully. Images: {', '.join(public_urls)}")
            ],
            "image_urls": public_urls,
            "code_status": True,
            "code_error": None,
        }
    except Exception as exc:
        return agent_retry_error(
            exc,
            state,
            error_key="code_error",
            status_key="code_status",
        )
