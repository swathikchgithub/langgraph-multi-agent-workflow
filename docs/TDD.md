# Technical Design Document
# Parts Identification & Routing Multi-Agent Workflow

**Version:** 1.0  
**Date:** 2026-06-20  
**Status:** In Development

---

## Project Structure

```
langgraph-multi-agent-workflow/
├── src/
│   ├── state.py              — WorkflowState TypedDict
│   ├── graph.py              — LangGraph workflow definition
│   ├── agents/
│   │   ├── supervisor.py     — query classification + routing
│   │   ├── part_identifier.py — catalog search + fuzzy match
│   │   ├── serial_resolver.py — PO/batch serial recovery
│   │   ├── router.py         — BU assignment
│   │   ├── action_recommender.py — instruction generation
│   │   ├── escalation.py     — human-in-the-loop package
│   │   ├── supply_chain.py   — supply chain Q&A
│   │   ├── finance.py        — finance Q&A
│   │   └── synthesizer.py    — cross-domain answer fusion
│   ├── tools/
│   │   └── catalog_tools.py  — catalog search, PO lookup, BU routing tools
│   └── data/
│       ├── parts_catalog.py  — mock parts catalog
│       ├── purchase_orders.py — mock PO records
│       └── business_units.py — mock BU definitions + routing rules
├── main.py                   — CLI entry point
├── tests/
│   └── test_workflow.py      — unit + integration tests
├── docs/                     — PRD, TDD, ARCHITECTURE, CODE_WALKTHROUGH
├── requirements.txt
└── .env.example
```

---

## State Design (`src/state.py`)

```python
from typing import TypedDict, Optional, Annotated
import operator

class WorkflowState(TypedDict):
    query: str
    part_description: str
    shipment_context: dict
    query_type: str                  # "parts" | "supply_chain" | "finance" | "cross"
    next: str

    # Part identification
    identified_part: Optional[dict]
    identification_confidence: float
    identification_source: str

    # Serial recovery
    recovered_serial: Optional[str]
    recovered_part_number: Optional[str]
    serial_source: str
    serial_confidence: float

    # Routing
    target_business_unit: Optional[str]
    priority: str
    contact_person: Optional[str]

    # Actions
    action_plan: Optional[str]
    storage_location: Optional[str]
    qc_required: bool

    # Escalation
    escalated: bool
    escalation_reason: Optional[str]
    investigation_package: Optional[dict]

    # Finance / SC answers
    supply_chain_answer: Optional[str]
    finance_answer: Optional[str]

    messages: Annotated[list, operator.add]
```

State is append-only for `messages`. All other fields are replaced (not merged) on each agent transition. This ensures deterministic state at each node.

---

## Graph Definition (`src/graph.py`)

```python
from langgraph.graph import StateGraph, END
from src.state import WorkflowState
from src.agents import (
    supervisor, part_identifier, serial_resolver,
    router, action_recommender, escalation,
    supply_chain, finance, synthesizer
)

def build_graph() -> StateGraph:
    workflow = StateGraph(WorkflowState)

    # Register nodes
    workflow.add_node("supervisor", supervisor.run)
    workflow.add_node("part_identifier", part_identifier.run)
    workflow.add_node("serial_resolver", serial_resolver.run)
    workflow.add_node("router", router.run)
    workflow.add_node("action_recommender", action_recommender.run)
    workflow.add_node("escalation", escalation.run)
    workflow.add_node("supply_chain", supply_chain.run)
    workflow.add_node("finance", finance.run)
    workflow.add_node("synthesizer", synthesizer.run)

    # Entry
    workflow.set_entry_point("supervisor")

    # Supervisor routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next"],
        {
            "part_identifier": "part_identifier",
            "supply_chain": "supply_chain",
            "finance": "finance",
            "cross": "supply_chain",   # SC runs first, finance second
        }
    )

    # Parts flow
    workflow.add_edge("part_identifier", "serial_resolver")
    workflow.add_conditional_edges(
        "serial_resolver",
        lambda state: "router" if state["serial_confidence"] >= 0.7 else "escalation",
        {"router": "router", "escalation": "escalation"}
    )
    workflow.add_edge("router", "action_recommender")
    workflow.add_edge("action_recommender", END)
    workflow.add_edge("escalation", END)

    # Finance/SC flow
    workflow.add_conditional_edges(
        "supply_chain",
        lambda state: "finance" if state["query_type"] == "cross" else END,
        {"finance": "finance", END: END}
    )
    workflow.add_edge("finance", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()
```

---

## Agent Design

### Supervisor Agent (`src/agents/supervisor.py`)

**Responsibility:** Classify the query and set the initial routing.

```python
SYSTEM = """
You are a supply chain AI supervisor at.
Classify the user query into one of:
- "parts": part identification, serial number recovery, routing
- "supply_chain": supplier performance, defect rates, lead times
- "finance": cost variance, reconciliation, budget analysis
- "cross": requires both supply chain and finance data

Return JSON: {"query_type": "...", "part_description": "...", "shipment_context": {...}}
"""
```

**Output contract:**
```python
class SupervisorOutput(BaseModel):
    query_type: Literal["parts", "supply_chain", "finance", "cross"]
    part_description: str
    shipment_context: dict
    next: str
```

---

### Part Identifier Agent (`src/agents/part_identifier.py`)

**Responsibility:** Match the described part to the parts catalog.

**Tools:**
- `search_catalog(description, category=None)` — fuzzy text search over catalog
- `lookup_by_po(po_number)` — get parts associated with a PO

**Confidence logic:**
```
Exact part number match  → 0.95
Category + size match    → 0.75–0.90
Description only match   → 0.60–0.75
No match                 → 0.0
```

**Output contract:**
```python
class PartIdentifierOutput(BaseModel):
    identified_part: Optional[dict]
    identification_confidence: float
    identification_source: str
```

---

### Serial Resolver Agent (`src/agents/serial_resolver.py`)

**Responsibility:** Recover serial and part numbers from PO, batch, or supplier records.

**Tools:**
- `lookup_po(po_number)` — fetch PO line items
- `lookup_batch(batch_id)` — fetch batch records with serial ranges
- `lookup_supplier_shipment(supplier_id, date_range)` — recent shipments

**Recovery logic:**
```
PO match + single part type → assign serial from range → confidence 0.95
PO match + multiple part types → narrow by description → confidence 0.75
Batch record only → confidence 0.80
No PO, description only → confidence 0.50
```

**Output contract:**
```python
class SerialResolverOutput(BaseModel):
    recovered_serial: Optional[str]
    recovered_part_number: Optional[str]
    serial_source: str
    serial_confidence: float
```

---

### Router Agent (`src/agents/router.py`)

**Responsibility:** Map identified part to the correct business unit.

**Routing rules (in `data/business_units.py`):**
```python
ROUTING_RULES = {
    "brake_system": {"bu": "Safety Systems Team", "priority": "critical"},
    "sensor_hardware": {"bu": "Sensor Integration Team", "priority": "high"},
    "suspension": {"bu": "Chassis Engineering", "priority": "high"},
    "electrical": {"bu": "Electrical Systems", "priority": "normal"},
    "body_panels": {"bu": "Body Assembly", "priority": "normal"},
}
```

**Output contract:**
```python
class RouterOutput(BaseModel):
    target_business_unit: str
    priority: Literal["critical", "high", "normal"]
    contact_person: str
    storage_location: str
    qc_required: bool
```

---

### Action Recommender Agent (`src/agents/action_recommender.py`)

**Responsibility:** Generate step-by-step instructions for the receiving team.

**Prompt inputs:** identified part + serial + business unit + priority + QC requirement

**Output:** numbered action plan with:
1. Label application instructions
2. Storage location
3. Notification steps (who to contact, how)
4. QC checklist (if required)
5. ERP entry instructions
6. Deadline (based on priority)

---

### Escalation Agent (`src/agents/escalation.py`)

**Responsibility:** Package all gathered context for human specialist review.

**Triggered when:** `serial_confidence < 0.7`

**Output:** investigation package containing:
- All context gathered so far
- Closest catalog matches (top 3)
- Suggested manual lookup steps
- Specialist contact information
- Urgency flag based on part category

---

## Tools (`src/tools/catalog_tools.py`)

```python
@tool
def search_catalog(description: str, category: str = None) -> list[dict]:
    """Search the parts catalog by description. Returns top 5 matches with scores."""

@tool
def lookup_po(po_number: str) -> dict:
    """Look up a purchase order by number. Returns line items with part numbers."""

@tool
def lookup_batch(batch_id: str) -> dict:
    """Look up batch record. Returns serial number range and part details."""

@tool
def get_business_unit_info(part_category: str) -> dict:
    """Get business unit assignment and routing rules for a part category."""

@tool
def get_supplier_shipments(supplier_id: str, days_back: int = 30) -> list[dict]:
    """Get recent shipments from a supplier."""

@tool
def get_defect_rates(supplier_id: str = None, part_category: str = None) -> dict:
    """Get defect rates by supplier or part category."""

@tool
def get_cost_variance(account_code: str, period: str) -> dict:
    """Get budget vs actual variance for an account."""
```

---

## Mock Data Design

### Parts Catalog (10 representative parts)
```python
{
    "part_number": "FSB-2024-L",
    "name": "Front Sensor Mounting Bracket",
    "category": "sensor_hardware",
    "vehicle_model": "ZX1",
    "supplier_id": "SUP-001",
    "dimensions": {"length_cm": 30, "weight_kg": 0.8},
    "serial_prefix": "SN-FSB",
    "safety_critical": True,
    "storage_requirements": "Dry, <25°C, Bin S-14"
}
```

### Purchase Orders (5 POs with line items)
```python
{
    "po_number": "PO-2024-0445",
    "supplier_id": "SUP-001",
    "supplier_name": "Acme Forgings",
    "order_date": "2024-03-10",
    "line_items": [
        {
            "part_number": "FSB-2024-L",
            "quantity": 50,
            "batch_id": "B2024-0315",
            "serial_range": {"start": "SN-FSB-0445-001", "end": "SN-FSB-0445-050"}
        }
    ]
}
```

---

## LLM Configuration

```python
from anthropic import Anthropic

client = Anthropic()

def call_llm(system: str, user: str, tools: list = None) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=tools or []
    )
    return response
```

All agents use `temperature=0` (implicit default) for deterministic, factual outputs. Tool use is enabled per-agent based on what data access is needed.

---

## Error Handling

| Error | Handling |
|---|---|
| Catalog search returns no matches | Set confidence=0.0, route to escalation |
| PO number not found | Try supplier shipment lookup as fallback |
| LLM returns invalid JSON | Retry once with stricter prompt, then escalate |
| LLM API timeout | Escalate with timeout flag in investigation package |
| Unknown part category | Route to General Receiving BU with normal priority |

---

## Testing Strategy

### Unit tests (per agent)
```python
def test_part_identifier_exact_match():
    state = {"part_description": "FSB-2024-L front sensor bracket", "shipment_context": {}}
    result = part_identifier.run(state)
    assert result["identification_confidence"] >= 0.9

def test_serial_resolver_po_lookup():
    state = {"identified_part": {...}, "shipment_context": {"po_number": "PO-2024-0445"}}
    result = serial_resolver.run(state)
    assert result["recovered_part_number"] == "FSB-2024-L"
    assert result["serial_confidence"] >= 0.9

def test_escalation_triggered_on_low_confidence():
    state = {"serial_confidence": 0.4, ...}
    # graph routes to escalation
    assert result["escalated"] == True
```

### Integration test (full workflow)
```python
def test_full_parts_workflow():
    result = app.invoke({
        "query": "Received metal bracket from Acme Forgings with PO-2024-0445",
        ...
    })
    assert result["target_business_unit"] == "Sensor Integration Team"
    assert result["recovered_part_number"] == "FSB-2024-L"
    assert result["action_plan"] is not None
```

---

## Performance Targets

| Operation | Target |
|---|---|
| Catalog search (tool) | <50ms |
| PO lookup (tool) | <50ms |
| LLM call per agent | <5s |
| Full workflow (5 agents) | <25s P95 |
| Escalation path | <10s P95 |
