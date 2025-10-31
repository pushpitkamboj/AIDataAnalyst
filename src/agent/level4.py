from dotenv import load_dotenv
load_dotenv()

from e2b_code_interpreter import Sandbox
from langchain_core.messages import AIMessage
from typing_extensions import TypedDict
from typing import Annotated
from .graph_state import State
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

llm = init_chat_model("openai:gpt-4.1")

#LEFT TREE NODE
class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

prompt_db = """
You are an agent designed to interact with a SQL database.
Given an input question, and all the relevant information about the database is already present in state: {schema_context}.
create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain.

examples of prompts:
SELECT id, email, password, "createdAt", "updatedAt", username FROM "User" ORDER BY "createdAt" DESC LIMIT 3

#make sure to have the appropriate data type and information related to it, therefore always cross check

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the user prompt.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the database context to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
"""

prompt_csv = """ 
You are an agent designed to interact with a SQL database.
Given an input question, and all the relevant information about the database is already present in state: {schema_context}.
create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, return all

Since the data type is csv and we are using duckdb to run the SQL query on csv data, make sure to generate the query in
the following format:
EG:     
    SELECT Country, TotalSpent FROM read_csv_auto({csv_url})
    MAKE THIS EXTRA  PIECE `read_csv_auto({csv_url})` AS A TABLE NAME IN THE QUERY, SO THE QUERY CAN BE EXECUTED USING DUCKDB

You can order the results by a relevant column to return the most interesting
examples in the database.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the relevant data info to see what you
can query. Do NOT skip this step.
"""
    

def create_query_prompt(state: State) -> str:
    ans = ""
    if state.get("csv_url"):
        ans = prompt_csv.format(
            dialect=state["dialect"],
            schema_context= state["schema_context"],
            csv_url=state["csv_url"]
        )
        
    elif state.get("db_url"):
        ans = prompt_db.format(
            dialect=state["dialect"],
            schema_context = state["schema_context"],
        )
        
    return ans

    
def generate_query(state: State):
    prompt = create_query_prompt(state)
    
    system_message = {
        "role": "system",
        "content": prompt
    }
    
    structured_llm = llm.with_structured_output(QueryOutput)
    response = structured_llm.invoke([system_message] + state["messages"])

    query_message = AIMessage(
        content=f"Generated SQL query: {response['query']}",
    )
    
    return {
        "messages": [query_message],
        "query": response["query"]
    }
    
    
#RIGHT TREE NODE
def data_to_sandbox(state: State): #based on data input upload csv or db
    sbx = Sandbox.create()
        
    if state.get("db_url"):
        url = state["db_url"].replace("'", "'\\''")  # escape single quotes just in case
        command = f"echo 'DATABASE_URL={url}' > .env"
        sbx.commands.run(command)
        sbx.commands.run("pip install dotenv")
        sbx.commands.run("pip install sqlalchemy")
        sbx.commands.run("pip install psycopg2")
        # sbx.commands.run("pip install holoviews bokeh datashader")
        ai_msg = AIMessage(content= "the connection url has been uploaded to the sandbox")
        
        return {
            "messages": [ai_msg],
            "sandbox_id": sbx.get_info().sandbox_id
        }
        
    elif state.get("csv_url"):
        ai_msg = AIMessage(
            content = "the csv url is ready to generate the code"
        )
        
        return {
            "sandbox_id": sbx.get_info().sandbox_id,
            "messages": [ai_msg]
        }