import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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


@app.post("/query")
def run_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        state = initial_state(req.query.strip())
        result = get_graph().invoke(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "query_type": result.get("query_type"),
        "identified_part": result.get("identified_part"),
        "identification_confidence": result.get("identification_confidence"),
        "recovered_serial": result.get("recovered_serial"),
        "recovered_part_number": result.get("recovered_part_number"),
        "target_business_unit": result.get("target_business_unit"),
        "priority": result.get("priority"),
        "contact_person": result.get("contact_person"),
        "storage_location": result.get("storage_location"),
        "qc_required": result.get("qc_required"),
        "action_plan": result.get("action_plan"),
        "escalated": result.get("escalated"),
        "escalation_reason": result.get("escalation_reason"),
        "investigation_package": result.get("investigation_package"),
        "supply_chain_answer": result.get("supply_chain_answer"),
        "finance_answer": result.get("finance_answer"),
        "final_answer": result.get("final_answer"),
    }
