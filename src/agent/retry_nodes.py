from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from utils.settings import get_settings

from .graph_state import State

get_settings().apply_to_environment()

llm = init_chat_model(model="gpt-4o-mini")

MAX_RETRIES = 3

class CorrectedCode(BaseModel):
    code: str

def fix_query(state: State):
    """LLM call to rewrite SQL query based on error."""
    error = state.get("query_error")
    query = state.get("query")
    schema = state.get("schema_context")
    dialect = state.get("dialect")
    system_prompt = f"""You are a SQL expert. The following query failed with an error.
    Fix the query based on the error message.
    Database dialect: {dialect}
    Schema context: {schema}
    Original query:
    {query}
    Error:
    {error}
    Return ONLY the corrected SQL query, nothing else."""
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Fix this query")
    ])
    fixed_query = response.content.strip()
    # Remove markdown code blocks if present
    if fixed_query.startswith("```"):
        lines = fixed_query.split("\n")
        fixed_query = "\n".join(lines[1:-1])
    return {
        "query": fixed_query,
        "query_error": None,
        "messages": [AIMessage(content=f"Query fixed. Retrying with: {fixed_query}")]
    }


def fix_code(state: State):
    """LLM call to rewrite Python code based on error."""
    error = state.get("code_error")
    code = state.get("python_code")
    schema = state.get("schema_context")
    system_prompt = f"""You are a Python expert. The following code failed with an error.
    Fix the code based on the error message.
    Data schema context: {schema}
    Original code:
    {code}
    Error:
    {error}
Return ONLY the corrected Python code, nothing else.
    The code should generate a visualization using matplotlib/seaborn and save to png."""
    structured_llm = llm.with_structured_output(CorrectedCode)
    response = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Fix this code")
    ])
    return {
        "python_code": response.code,
        "code_error": None,
        "messages": [AIMessage(content=f"Code fixed. Retrying...")]
    }


def should_retry_query(state: State) -> str:
    """Decide whether to retry query or give up."""
    retry_count = state.get("retry_count", 0)
    query_error = state.get("query_error")
    if query_error and retry_count < MAX_RETRIES:
        return "fix_query"
    elif query_error:
        return "generate_answer_query"  # Give up, return error in answer
    return "generate_answer_query"


def should_retry_code(state: State) -> str:
    """Decide whether to retry code or give up."""
    code_error = state.get("code_error")
    if code_error:
        return "fix_code"
    return "generate_answer_viz"
