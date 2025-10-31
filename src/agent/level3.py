from pydantic import BaseModel
from typing import Literal
from langchain.chat_models import init_chat_model
from .graph_state import State
from .level4 import data_to_sandbox, generate_query
from langgraph.types import Command
from langchain_core.messages import AIMessage

llm = init_chat_model("openai:gpt-4.1")
class prompt_decision(BaseModel):
    analysis_type: Literal["sql", "visualization"]

def prompt_analysis(state: State):
    prompt = """
    take the prompt of the user, understand it and decide that the question should be answered by a sql query or it needs analysis and hence a grpahical response
    EG:
    1) give me the users who are below age 18 -> this can be answered by sql query
    2) compare the salaries of male and female employees who based on different city offices -> best reply to this query is through data visualization
    """
    
    structured_llm = llm.with_structured_output(prompt_decision)
    response = structured_llm.invoke(state["messages"] + [{"role": "system", "content": prompt}])
    analysis_type = response.analysis_type
    
    ai_msg = AIMessage(
        content=f"the response of the user query will be answered with {analysis_type}"
    )
    
    return {
        "message": [ai_msg],
        "decision": analysis_type
    }
    
