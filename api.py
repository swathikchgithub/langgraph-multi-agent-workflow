import json
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.graph import compile_graph
from src.state import initial_state

app = FastAPI(title="Multi-Agent Parts Workflow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = compile_graph()
    return _graph


class QueryRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


def _build_result(r: dict) -> dict:
    return {
        "query_type": r.get("query_type"),
        "identified_part": r.get("identified_part"),
        "identification_confidence": r.get("identification_confidence"),
        "recovered_serial": r.get("recovered_serial"),
        "recovered_part_number": r.get("recovered_part_number"),
        "target_business_unit": r.get("target_business_unit"),
        "priority": r.get("priority"),
        "contact_person": r.get("contact_person"),
        "storage_location": r.get("storage_location"),
        "qc_required": r.get("qc_required"),
        "action_plan": r.get("action_plan"),
        "escalated": r.get("escalated"),
        "escalation_reason": r.get("escalation_reason"),
        "investigation_package": r.get("investigation_package"),
        "supply_chain_answer": r.get("supply_chain_answer"),
        "finance_answer": r.get("finance_answer"),
        "final_answer": r.get("final_answer"),
    }


@app.post("/query")
def run_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        state = initial_state(req.query.strip())
        result = get_graph().invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return _build_result(result)


@app.post("/query/stream")
def stream_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    state = initial_state(req.query.strip())

    def generate():
        accumulated: dict = {}
        try:
            for event in get_graph().stream(state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    for k, v in node_output.items():
                        if k != "messages":
                            accumulated[k] = v
                    clean = {k: v for k, v in node_output.items() if k != "messages"}
                    payload = {"type": "agent", "agent": node_name, "update": clean}
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'result': _build_result(accumulated)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
