
from .graph_state import State
import os
from supabase import create_client, Client
import pandas as pd
from langchain_core.messages import AIMessage
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool


def extract_db_info(state: State):
    #url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db" #hosted local DB
    url = state.get("db_url")     
    print(f"the url is :{url}")
    db = SQLDatabase.from_uri(url) #https://python.langchain.com/api_reference/community/utilities/langchain_community.utilities.sql_database.SQLDatabase.html#langchain_community.utilities.sql_database.SQLDatabase.from_uri
    table_names = db.get_usable_table_names()
    list_col = InfoSQLDatabaseTool(db=db)
    db_info = {}
    
    try:
        for table_name in table_names:
            result = list_col.invoke({"table_names": table_name})
            db_info[table_name] = result    
    except:
        print("the DB is corrupted")

    response = AIMessage(
        content="all the relevant metadata about database has been generated and stored in the state",
    )
    
    state_update = {
        "schema_context": db_info,
        "messages": [response],
        "dialect": db.dialect
    }
    return state_update


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
