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

project_url = os.getenv("project_url")
api_key = os.getenv("api_key")

supabase: Client = create_client(project_url, api_key)
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
        return {"error": str(e)}

    return {"sql_query_output": df.to_dict(orient="records")}

#RIGHT NODE    
import base64
def run_code(state: State):
    sbx = Sandbox.connect(state["sandbox_id"])
        
    image_exist = False
    execution = sbx.run_code(state["python_code"])

    if execution.error:
        not_worked = AIMessage(
            content=f"the execution of the code inside sandbox stopped due to error -> {execution.error}"
        )
        
        return {
            "messages": [not_worked],
            # "code_error": [execution.error],
            # "code_status": False
        }
        
    # image_files = []
    # result_idx = 0
    # for result in execution.results:
    #     if result.png:
    #         file_name = f'chart-{result_idx}.png'
    #         with open(file_name, 'wb') as f:
    #             f.write(base64.b64decode(result.png))
    #         print(f'Chart saved to {file_name}')
    #         image_files.append(file_name)
    #         result_idx += 1

    # worked = AIMessage(
    #     content=f"the code has been executed successfully by the sandbox and the resulted image file locations are: {', '.join(image_files)}"
    # )

    # return {
    #     "messages": [worked],
    #     "image_locations": image_files
    # }
    public_urls = []
    result_idx = 0

    for result in execution.results:
        if not result.png:
            continue

        img_bytes = base64.b64decode(result.png)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        filename = f"chart-{result_idx}-{timestamp}.png"
        path_in_bucket = f"{filename}" #in the root of the folder
        
        res = supabase.storage.from_("data_image").upload(path_in_bucket, img_bytes, {"content-type": "image/png"})

        public_url = supabase.storage.from_("data_image").get_public_url(path_in_bucket)
        public_urls.append(public_url)
        
        result_idx += 1

    # Prepare message to return (similar to your original)
    worked = AIMessage(
        content=(
            f"the code has been executed successfully by the sandbox and the resulted image file locations are: "
            + ", ".join(public_urls) + f"{execution.results}"
        )
    )
    
    sbx.kill()

    return {
        "messages": [worked],
        "image_urls": public_urls,
        # "code_status": True
    }