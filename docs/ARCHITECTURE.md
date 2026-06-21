# Architecture — Parts Identification & Routing Workflow

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                                │
│         (part description / shipment context / query)            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                              │
│   • Classifies query (parts | finance | supply chain)           │
│   • Determines initial routing                                   │
│   • Sets workflow context                                        │
└──────┬──────────────────┬──────────────────────┬───────────────┘
       │                  │                      │
       ▼                  ▼                      ▼
┌─────────────┐  ┌────────────────┐   ┌──────────────────┐
│   Parts     │  │ Supply Chain   │   │   Finance        │
│ Identifier  │  │    Agent       │   │    Agent         │
│             │  │                │   │                  │
│ • Catalog   │  │ • Defect rates │   │ • Recon data     │
│   search    │  │ • Supplier     │   │ • Cost variance  │
│ • Fuzzy     │  │   performance  │   │ • Budget vs      │
│   match     │  │ • Lead times   │   │   actuals        │
│ • Confidence│  │                │   │                  │
└──────┬──────┘  └────────┬───────┘   └────────┬─────────┘
       │                  │                     │
       ▼                  └──────────┬──────────┘
┌─────────────┐                      │
│   Serial    │                      ▼
│  Resolver   │         ┌────────────────────────┐
│             │         │   Synthesizer Agent    │
│ • PO lookup │         │   (finance + SC only)  │
│ • Batch     │         └────────────────────────┘
│   records   │
│ • Supplier  │
│   history   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│         Confidence Check             │
│                                      │
│   ≥ 0.7  ──────────────────────┐    │
│   < 0.7  ──────────┐           │    │
└────────────────────┼───────────┼────┘
                     │           │
                     ▼           ▼
            ┌──────────────┐  ┌──────────────────┐
            │  Escalation  │  │  Router Agent    │
            │    Agent     │  │                  │
            │              │  │ • BU assignment  │
            │ • Human flag │  │ • Priority level │
            │ • Package    │  │ • Contact info   │
            │   context    │  └────────┬─────────┘
            └──────────────┘           │
                                       ▼
                              ┌──────────────────┐
                              │  Action          │
                              │  Recommender     │
                              │                  │
                              │ • Step-by-step   │
                              │   instructions   │
                              │ • Storage loc    │
                              │ • QC checklist   │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  Final Output    │
                              │                  │
                              │ • Part ID        │
                              │ • Serial/PN      │
                              │ • Business unit  │
                              │ • Action plan    │
                              │ • Confidence     │
                              └──────────────────┘
```

---

## LangGraph State Machine

```
                    ┌─────────┐
                    │  START  │
                    └────┬────┘
                         │
                         ▼
                  ┌────────────┐
                  │ supervisor │
                  └─────┬──────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
           ▼            ▼            ▼
    ┌─────────────┐  ┌────────┐  ┌─────────┐
    │part_identify│  │supply_ │  │finance_ │
    └──────┬──────┘  │chain   │  │agent    │
           │         └───┬────┘  └────┬────┘
           ▼             └─────┬──────┘
    ┌─────────────┐            ▼
    │serial_      │     ┌─────────────┐
    │resolver     │     │synthesizer  │
    └──────┬──────┘     └──────┬──────┘
           │                   │
           ▼                   ▼
    ┌─────────────┐          ┌─────┐
    │ confidence  │          │ END │
    │   check     │          └─────┘
    └──────┬──────┘
     ≥0.7  │  <0.7
    ┌───────┘   └────────┐
    ▼                    ▼
┌────────┐        ┌────────────┐
│router  │        │escalation  │
└───┬────┘        └──────┬─────┘
    │                    │
    ▼                    ▼
┌────────────┐         ┌─────┐
│action_     │         │ END │
│recommender │         └─────┘
└──────┬─────┘
       │
       ▼
    ┌─────┐
    │ END │
    └─────┘
```

---

## Agent Responsibilities

| Agent | Input | Output | LLM call |
|---|---|---|---|
| Supervisor | Raw query | Route decision + query type | Yes |
| Part Identifier | Description + context | Part match + confidence | Yes + tool |
| Serial Resolver | Part match + shipment data | Serial/PN + source | Yes + tool |
| Router | Identified part | Business unit + priority | Yes |
| Action Recommender | Part + BU + serial | Step-by-step instructions | Yes |
| Escalation | Full state | Investigation package | Yes |
| Supply Chain | Query | SC data answer | Yes + tool |
| Finance | Query | Finance data answer | Yes + tool |
| Synthesizer | SC + Finance answers | Combined response | Yes |

---

## State Schema

```python
class WorkflowState(TypedDict):
    # Input
    query: str
    part_description: str
    shipment_context: dict          # PO number, supplier, date, quantity

    # Identification
    identified_part: Optional[dict] # part_number, name, category, specs
    identification_confidence: float
    identification_source: str      # "catalog_match" | "po_lookup" | "fuzzy"

    # Serial recovery
    recovered_serial: Optional[str]
    recovered_part_number: Optional[str]
    serial_source: str              # "purchase_order" | "batch_record" | "supplier"
    serial_confidence: float

    # Routing
    target_business_unit: Optional[str]
    priority: str                   # "critical" | "high" | "normal"
    contact_person: Optional[str]

    # Action
    action_plan: Optional[str]
    storage_location: Optional[str]
    qc_required: bool

    # Escalation
    escalated: bool
    escalation_reason: Optional[str]
    investigation_package: Optional[dict]

    # Finance / SC
    supply_chain_answer: Optional[str]
    finance_answer: Optional[str]

    # Control
    query_type: str                 # "parts" | "supply_chain" | "finance" | "cross"
    next: str                       # next node to execute
    messages: Annotated[list, operator.add]
```

---

## Data Flow

```
Input: "Received a metal bracket, approx 30cm, looks like a mounting component,
        came with PO-2024-0445 from Acme Forgings"

Supervisor:
  → query_type = "parts"
  → next = "part_identifier"

Part Identifier:
  → searches catalog for "metal bracket mounting 30cm"
  → matches: "Front Sensor Mounting Bracket" (FSB-2024-L), confidence: 0.82
  → next = "serial_resolver"

Serial Resolver:
  → looks up PO-2024-0445
  → finds: 50 units of FSB-2024-L, batch B2024-0315
  → recovers: serial SN-FSB-0445-001 through SN-FSB-0445-050
  → confidence: 0.95
  → next = "router" (confidence ≥ 0.7)

Router:
  → FSB-2024-L → category: sensor_hardware → BU: Sensor Integration Team
  → priority: high (sensor component)
  → contact: sensor.integration@company.com

Action Recommender:
  → "1. Apply recovered label SN-FSB-0445-001
     2. Store in Bin S-14, Warehouse B
     3. Notify Sensor Integration Team via Slack #parts-receiving
     4. Schedule QC inspection within 4 hours
     5. Log in ERP under PO-2024-0445"

Output: Structured result with all fields populated
```

---

## Technology Stack

| Component | Technology | Reason |
|---|---|---|
| Orchestration | LangGraph | Native multi-agent state machine, conditional routing |
| LLM | Claude (`claude-sonnet-4-6`) | Tool use, structured output, low hallucination |
| Language | Python 3.11+ | LangGraph native, ML ecosystem |
| Data | Mock JSON (in-memory) | No infra needed for demo |
| CLI | Python argparse | Simple demo interface |
| Tests | pytest | Standard Python testing |

---

## Key Design Decisions

**1. Why LangGraph over LangChain LCEL?**
LangGraph provides a proper state machine with conditional edges and cycles. LCEL is linear. Multi-agent workflows with branching (confidence check → escalate OR route) need a graph, not a chain.

**2. Why separate agents for identification vs serial resolution?**
Single Responsibility Principle. Part identification uses catalog fuzzy matching. Serial recovery uses PO/batch record lookup. They use different tools, different prompts, and can fail independently.

**3. Why confidence threshold for escalation?**
Safety-critical components cannot be misrouted. A brake caliper going to the wrong business unit is a production safety issue. Human-in-the-loop at low confidence is a hard requirement.

**4. Why structured JSON output from all agents?**
Downstream agents consume upstream outputs programmatically. Free-text output between agents creates parsing failures. Pydantic models enforce the contract.
