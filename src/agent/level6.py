from .graph_state import State
import duckdb
from langchain_core.messages import AIMessage
import datetime
from supabase import create_client, Client
import os
from langchain_community.utilities import SQLDatabase
import pandas as pd
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

MAX_RETRIES = 3

#LEFT NODE
def run_query(state: State):
    """Execute SQL query on CSV or DB and return DataFrame."""
    query = state.get("query")
    df = None
    
    try:
        if state.get("csv_url"):
            con = duckdb.connect()
            df = con.execute(query).df()

        elif state.get("db_url"):
            db = SQLDatabase.from_uri(state["db_url"])
            df = pd.read_sql(query, db._engine)

    except Exception as e:
        return {
            "query_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

    return {
        "sql_query_output": df.to_dict(orient="records"),
        "query_error": None
    }

#RIGHT NODE    
import base64
def run_code(state: State):
    sbx = Sandbox.connect(state["sandbox_id"])
    
    try:
        execution = sbx.run_code(state["python_code"])

        if execution.error:
            return {
                "code_error": str(execution.error),
                "code_status": False,
                "retry_count": state.get("retry_count", 0) + 1
            }
            
        public_urls = []
        result_idx = 0

        for result in execution.results:
            if not result.png:
                continue

            img_bytes = base64.b64decode(result.png)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            filename = f"chart-{result_idx}-{timestamp}.png"
            path_in_bucket = f"{filename}"
            
            res = supabase.storage.from_("data_image").upload(path_in_bucket, img_bytes, {"content-type": "image/png"})
            public_url = supabase.storage.from_("data_image").get_public_url(path_in_bucket)
            public_urls.append(public_url)
            
            result_idx += 1

        worked = AIMessage(
            content=f"Code executed successfully. Images: {', '.join(public_urls)}"
        )
        
        sbx.kill()

        return {
            "messages": [worked],
            "image_urls": public_urls,
            "code_status": True,
            "code_error": None
        }
        
    except Exception as e:
        return {
            "code_error": str(e),
            "code_status": False,
            "retry_count": state.get("retry_count", 0) + 1
        }