from .graph_state import State
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4.1")

#RIGHT NODE
class code_format(TypedDict):
    code: Annotated[str, ..., "the python code to run"] 
    
def generate_code(state: State):
    viz_system_prompt = ""
    
    if state.get("csv_url"):
        viz_system_prompt = f"""
            You are a helpful assistant that can write code in python. 
            i have the csv file. its link is {state["csv_url"]}
            eg of code:
            import pandas as pd
            import matplotlib.pyplot as plt

            # CSV hosted on Supabase (public URL)
            url = "{state["csv_url"]}"

            # Load CSV into DataFrame
            df = pd.read_csv(url)

            # Basic sanity check
            print(df)

            # Plot bar graph
            plt.figure(figsize=(8,5))
            plt.bar(df["Country"], df["TotalSpent"])
            plt.title("Total Spending by Country")
            plt.xlabel("Country")
            plt.ylabel("Total Spent")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

            the metadata of it is: {state["schema_context"]}
            Write Python code that analyzes the dataset based on the user's request and produces right chart accordingly
            """
    elif state.get("db_url"):
        
        viz_system_prompt = f"""
            i have the connection url stored inside .env file in the sandbox as DATABASE_URL
            the metadata of the database is: {state["schema_context"]}
            since the database has a lot of inter connected table, create the appropriate dataframe joining the relevant tables with 
            the help of {state["dialect"]} 
            eg: if the dialect is 
            import os
            from dotenv import load_dotenv
            from sqlalchemy import create_engine, text 
            import pandas as pd
            

            # Load .env file
            load_dotenv()

            # Read DATABASE_URL from .env
            db_url = os.getenv("DATABASE_URL")

            if not db_url:
                raise ValueError("DATABASE_URL not found in .env. Go fix your typos.")

            # Create SQLAlchemy engine
            engine = create_engine(db_url)

            # Example query
            query = text("
            SELECT c.customer_id, c.first_name, c.last_name, o.item, o.amount, s.status
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.customer_id
            LEFT JOIN shippings s ON s.customer = c.customer_id
            LIMIT 10
            ")

            # Run query into a Pandas DataFrame
            with engine.connect() as conn:
                df = pd.read_sql_query(query, conn)
            After this, Write Python code that analyzes the dataset based on the user's request and produces right charts/graphs/visuals accordingly
        """
    
    structured_llm = llm.with_structured_output(code_format)
    response = structured_llm.invoke([{"role": "system", "content": viz_system_prompt}] + state["messages"])
    
    ai_message_code = AIMessage(
        content = "python code has been generated successfully for the visualization and instance has also been created",
    )
    
    return {
        "messages": [ai_message_code],
        "python_code": response["code"],
    }
    
    
#LEFT NODE
check_query_system_prompt = """
You are a SQL expert with a strong attention to detail.
Double check the {dialect} query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes,
just reproduce the original query.

You will call the appropriate tool to execute the query after running this check.
"""

def check_prompt(state: State):
    return check_query_system_prompt.format(
        dialect=state["dialect"],
    )
    
class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: str
    
def check_query(state: State):
    system_message = {
        "role": "system",
        "content": check_prompt(state),
    }
    structured_llm = llm.with_structured_output(QueryOutput)
    response = structured_llm.invoke([state["query"]] + [system_message])
    
    ai_msg = AIMessage(
        content = "the query is checked"
    )
    
    return {
        "query": response["query"],
        "messages": [ai_msg]
    }
