from typing import Literal

from langgraph.graph import END, START, StateGraph

from utils.settings import get_settings

from .code_generation import check_query, generate_code
from .data_extraction import extract_csv_info, extract_db_info
from .execution import run_code, run_query
from .graph_state import State
from .intent import prompt_analysis
from .query_generation import data_to_sandbox, generate_query
from .response_generation import generate_answer_query, generate_answer_viz
from .retry_nodes import fix_code, fix_query, should_retry_code, should_retry_query
from .routing import routing_fn

get_settings().apply_to_environment()


def decision_fn(state: State) -> Literal["generate_query", "data_to_sandbox"]:
    if state["decision"] == "sql":
        return "generate_query"
    if state["decision"] == "visualization":
        return "data_to_sandbox"
    raise ValueError(f"Unsupported analysis decision: {state['decision']}")


agent_graph = StateGraph(State)

agent_graph.add_node(extract_csv_info)
agent_graph.add_node(extract_db_info)
agent_graph.add_node(prompt_analysis)
agent_graph.add_node(generate_code)
agent_graph.add_node(run_code)
agent_graph.add_node(fix_code)
agent_graph.add_node(generate_answer_viz)
agent_graph.add_node(generate_query)
agent_graph.add_node(check_query)
agent_graph.add_node(run_query)
agent_graph.add_node(fix_query)
agent_graph.add_node(generate_answer_query)
agent_graph.add_node(data_to_sandbox)

agent_graph.add_conditional_edges(
    START,
    routing_fn,
    {"csv": "extract_csv_info", "database": "extract_db_info"},
)
agent_graph.add_edge("extract_db_info", "prompt_analysis")
agent_graph.add_edge("extract_csv_info", "prompt_analysis")
agent_graph.add_conditional_edges("prompt_analysis", decision_fn)

agent_graph.add_edge("generate_query", "check_query")
agent_graph.add_edge("check_query", "run_query")
agent_graph.add_conditional_edges(
    "run_query",
    should_retry_query,
    {
        "fix_query": "fix_query",
        "generate_answer_query": "generate_answer_query",
    },
)
agent_graph.add_edge("fix_query", "run_query")
agent_graph.add_edge("generate_answer_query", END)

agent_graph.add_edge("data_to_sandbox", "generate_code")
agent_graph.add_edge("generate_code", "run_code")
agent_graph.add_conditional_edges(
    "run_code",
    should_retry_code,
    {
        "fix_code": "fix_code",
        "generate_answer_viz": "generate_answer_viz",
    },
)
agent_graph.add_edge("fix_code", "run_code")
agent_graph.add_edge("generate_answer_viz", END)

app = agent_graph.compile()
