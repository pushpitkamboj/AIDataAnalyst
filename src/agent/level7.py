import requests
import base64
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from .graph_state import State
from dotenv import load_dotenv
load_dotenv()
from langchain.chat_models import init_chat_model
import pandas as pd

llm = init_chat_model("openai:gpt-4.1")
def generate_answer_query(state: State):
    """Answer question using retrieved information as context."""
    # query = state["query"]
    # prompt = (
    #     f"analyze the query: {query} and give an insightful 1 line statement. do not give info like run on this using duckdb or whatever, just think the outcome of query is something and u get back"
    # )
    # response = llm.invoke(prompt)
    return {"result": state["sql_query_output"]}


def generate_answer_viz(state: State):
    model = init_chat_model(model="gpt-4o")
    urls = state.get("image_urls")
    if not urls:
        raise ValueError("state['image_urls'] is empty")

    image_parts = []
    for u in urls:
        r = requests.get(u, timeout=10)
        r.raise_for_status()
        ct = r.headers.get("content-type") or "image/png"
        b64 = base64.b64encode(r.content).decode("utf-8")
        image_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:{ct};base64,{b64}"}
        })

    system_msg = SystemMessage(content=f"You are a data analyst. Inspect the provided chart images and return with a good summarized paragraph about it, the content should be purely human readable with no mdx or any other syntax. If no images are found in ur context, politely reply that couldn't generate the image")
    human_msg = HumanMessage(content=[{"type":"text","text":"Analyze these charts:"}] + image_parts)

    resp = model.invoke([system_msg, human_msg])
    result = resp.content + state["image_urls"][0]
    return {
        "result": result
    }

# if __name__ == "__main__":
#     val = generate_answer_viz()
#     print(val)