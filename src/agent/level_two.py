
from .graph_state import State
import os
from supabase import create_client, Client
import pandas as pd
from langchain_core.messages import AIMessage
from sqlalchemy import create_engine, inspect, MetaData


def extract_db_info(state: State):
    """Extract database schema metadata using SQLAlchemy."""
    url = state.get("db_url")
    print(f"the url is: {url}")
    
    engine = create_engine(url)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    schema_context = {}
    
    try:
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_pk_constraint(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            indexes = inspector.get_indexes(table_name)
            
            # Build column info
            column_info = []
            for col in columns:
                col_data = {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default")) if col.get("default") else None,
                }
                column_info.append(col_data)
            
            # Build create statement
            col_defs = []
            for c in column_info:
                col_defs.append(f"{c['name']} {c['type']}")
            create_stmt = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
            
            # Build table metadata
            schema_context[table_name] = {
                "columns": column_info,
                "primary_keys": primary_keys.get("constrained_columns", []),
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {"name": idx["name"], "columns": idx["column_names"], "unique": idx["unique"]}
                    for idx in indexes
                ],
                "create_statement": create_stmt
            }
        
        # Detect dialect from engine
        dialect = engine.dialect.name
        
    except Exception as e:
        print(f"Error extracting DB schema: {e}")
        schema_context = {"error": str(e)}
        dialect = "unknown"
    finally:
        engine.dispose()

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
