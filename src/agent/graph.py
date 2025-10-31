from dotenv import load_dotenv
load_dotenv()
import requests
import pandas as pd
import duckdb
import base64

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase #https://python.langchain.com/api_reference/community/utilities/langchain_community.utilities.sql_database.SQLDatabase.html#langchain_community.utilities.sql_database.SQLDatabase, #Utilities are the integrations with third-part systems and packages.
# from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from e2b_code_interpreter import Sandbox

from langsmith import traceable

from typing import Annotated, Literal #its for using validators eg: Age = Annotated[int, Field(ge=18)] 
from typing_extensions import TypedDict



from .level_two import extract_csv_info, extract_db_info
from .level1 import routing_fn
from .level3 import prompt_analysis
from .level4 import generate_query, data_to_sandbox
from .level5 import check_query, generate_code
from .level6 import run_query, run_code
from .level7 import generate_answer_query, generate_answer_viz

from .graph_state import State
    
    # db_instance: SQLDatabase
    # query: str
    # result: pd.DataFrame
    # python_code: str
    # dialect: str #for csv it is postgres flavored ANSI SQL
    # image_locations: list[str]
    # analysis_type: Literal["sql", "visualization"]
    # data_file_location: str
    # sandbox_instance: Sandbox
    # data_format: Literal["database", "csv"]
    
#now generate the code, u have the context of both the data type formats



# def data_format_decision(state: State): #based on user prompt the model will decide to go to extract_db_info OR extract csv info
#     return {
#         "message": "based on analysis the input data is of sqlite format",
#         "dialect": "sqlite",
#         "data_format": "csv"
#         }

agent_graph = StateGraph(State)
# agent_graph.add_node(data_format_decision)
agent_graph.add_node(extract_csv_info)
agent_graph.add_node(extract_db_info)

agent_graph.add_node(prompt_analysis) #the deciding factor to go to query conor visualization
agent_graph.add_node(generate_code)
agent_graph.add_node(run_code)
agent_graph.add_node(generate_answer_viz)

agent_graph.add_node(generate_query)
agent_graph.add_node(check_query)
agent_graph.add_node(run_query)
agent_graph.add_node(generate_answer_query)
agent_graph.add_node(data_to_sandbox)

agent_graph.add_conditional_edges(START, routing_fn, {"csv": "extract_csv_info", "database": "extract_db_info"})
agent_graph.add_edge("extract_db_info", "prompt_analysis")
agent_graph.add_edge("extract_csv_info", "prompt_analysis")

def decision_fn(state: State) -> Literal["generate_query", "data_to_sandbox"]:
    if state["decision"] == "sql":
        return "generate_query"
    if state["decision"] == "visualization":
        return "data_to_sandbox"
    
agent_graph.add_conditional_edges("prompt_analysis", decision_fn)

agent_graph.add_edge("generate_query", "check_query")
agent_graph.add_edge("check_query", "run_query")
agent_graph.add_edge("run_query", "generate_answer_query")
agent_graph.add_edge("generate_answer_query", END)

agent_graph.add_edge("data_to_sandbox", "generate_code")
agent_graph.add_edge("generate_code", "run_code")

# def loop_code_execution(state: State) -> Literal["generate_code", "generate_answer_viz"]:
#     if state.get("code_status") == False:
#         return "generate_code"
#     if state.get("code_status") == True:
        
#         sbx = Sandbox.connect(state["sandbox_id"])
#         sbx.kill()
#         return "generate_answer_viz"
    
# agent_graph.add_conditional_edges("run_code", loop_code_execution) #generate code OR generate answer viz
agent_graph.add_edge("run_code", "generate_answer_viz")
agent_graph.add_edge("generate_answer_viz", END)

app = agent_graph.compile()

@traceable
def main():
    config = {"configurable": {"thread_id": "traveler_456"}, "recursion_limit": 3}
    user_query = {"messages": [{"role": "user", "content": "give me the latest last 3 users with all there details"}], "db_url": "postgresql://blog-assignment_owner:npg_QGj8zmUExCu4@ep-red-truth-a4blfydv-pooler.us-east-1.aws.neon.tech/blog-assignment?sslmode=require&channel_binding=require"}
    full_plan = app.invoke(user_query, config)
    
    
from IPython.display import Image, display
try:
    with open("graph_arch.png", "wb") as f:
        f.write(app.get_graph().draw_png())
except Exception:
    # This requires some extra dependencies and is optional
    print("couldnt print")
    
if __name__ == "__main__":
    main()