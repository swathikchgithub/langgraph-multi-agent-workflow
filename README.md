# Multi-Agent Parts Workflow

A LangGraph-based multi-agent system that identifies untagged parts arriving at the
warehouse, recovers serial and part numbers from PO records, routes each part to the
correct business unit, and generates action instructions for the receiving team.
Also handles supply chain and finance queries.

## Problem Statement

Parts arrive at without serial numbers or part number labels. Without identification:
- Parts can't be routed to the correct business unit
- Receiving teams don't know how to handle, store, or inspect them
- Inventory systems can't be updated
- Finance can't reconcile PO line items

This system solves the identification, recovery, routing, and action-planning problem
end-to-end using a multi-agent AI workflow.

## Architecture

```
User Query
    │
    ▼
┌─────────────┐
│  Supervisor │  classifies query type, extracts context
└──────┬──────┘
       │
  ┌────┴─────────────────────────────────┐
  │                          │           │
  ▼                          ▼           ▼
Parts Flow             Supply Chain   Finance
  │                          │           │
  ▼                          └─────┬─────┘
Part Identifier                    │
  │                          Synthesizer
  ├─ confidence >= 0.7
  │
  ▼
Serial Resolver
  │
  ├─ confidence >= 0.7
  │
  ▼
 Router → Action Recommender
  │
  └── OR ──► Escalation (low confidence)
```

### Agents

| Agent | Role |
|---|---|
| Supervisor | Classifies query, extracts PO/supplier context |
| Part Identifier | Matches parts to catalog using description + context |
| Serial Resolver | Recovers serial/part numbers from PO records |
| Router | Assigns part to business unit with storage location |
| Action Recommender | Generates step-by-step handling instructions |
| Escalation | Creates investigation package for human review |
| Supply Chain | Answers supplier defect rate / delivery queries |
| Finance | Answers cost variance / reconciliation queries |
| Synthesizer | Combines multi-domain answers into one response |

### Confidence Thresholding

Both identification and serial recovery produce a confidence score (0.0–1.0).
- Score **≥ 0.70** → automated processing continues
- Score **< 0.70** → escalated to human specialist with a quarantine package

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Usage

```bash
# Interactive mode
python main.py

# Single query
python main.py "A silver bracket arrived without labels, came with PO-2024-0445"

# Run all demo scenarios
python main.py --demo
```

## Demo Scenarios

| Scenario | Expected outcome |
|---|---|
| Part + PO number | Identified → serial recovered → routed → action plan |
| Part description only | Identified from catalog → routed (or escalated if low confidence) |
| Supplier defect rates | Supply chain analysis with flagged suppliers |
| Cost variance query | Finance analysis with over/under budget breakdown |
| Cross supply chain + finance | Both agents run, synthesizer combines results |

## Running Tests

```bash
pytest tests/ -v

# With coverage
pip install pytest-cov
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Project Structure

```
langgraph-multi-agent-workflow/
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example
├── docs/
│   ├── PRD.md                 # Product requirements
│   ├── ARCHITECTURE.md        # System design + diagrams
│   ├── TDD.md                 # Technical design document
│   └── CODE_WALKTHROUGH.md    # Code review guide
├── src/
│   ├── state.py               # WorkflowState TypedDict
│   ├── graph.py               # LangGraph StateGraph definition
│   ├── agents/
│   │   ├── llm.py             # Claude client + agentic loop
│   │   ├── supervisor.py
│   │   ├── part_identifier.py
│   │   ├── serial_resolver.py
│   │   ├── router.py
│   │   ├── action_recommender.py
│   │   ├── escalation.py
│   │   ├── supply_chain.py
│   │   ├── finance.py
│   │   └── synthesizer.py
│   ├── tools/
│   │   └── catalog_tools.py   # Tool functions + Claude tool definitions
│   └── data/
│       ├── parts_catalog.py   # 10 mock parts
│       ├── purchase_orders.py # 5 POs + supplier metrics + finance data
│       └── business_units.py  # Routing rules by part category
└── tests/
    └── test_workflow.py       # Unit + integration tests
```

## Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — agent orchestration graph
- **[Anthropic Claude](https://www.anthropic.com)** — LLM with native tool_use
- **Python 3.11+**

## License

MIT
