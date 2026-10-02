import uuid
from typing import Any

from fastapi import APIRouter

from agent.graph import app as graph_app
from api.schemas import QueryRequest
from utils.errors import bad_request, run_route

router = APIRouter()


@router.post("/query")
async def query(payload: QueryRequest) -> dict[str, Any]:
    async def handler() -> dict[str, Any]:
        if payload.db_url:
            return await _run_agent_query(payload, "db_url", payload.db_url)
        if payload.csv_url:
            return await _run_agent_query(payload, "csv_url", payload.csv_url)
        bad_request("Provide either csv_url or db_url")

    return await run_route("query", handler)


async def _run_agent_query(
    payload: QueryRequest,
    source_key: str,
    source_value: str,
) -> dict[str, Any]:
    result = await graph_app.ainvoke(
        input={
            "messages": [{"role": "user", "content": payload.query}],
            source_key: source_value,
        },
        config={
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 18,
        },
    )
    response = {"message": result["result"]}
    if "image_urls" in result:
        response["image_urls"] = result["image_urls"]
    return response
