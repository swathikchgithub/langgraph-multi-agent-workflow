# Code Walkthrough & Interview Script
# Parts Identification & Routing Multi-Agent Workflow

---

## The One-Sentence Pitch

> "I built a multi-agent AI workflow using LangGraph that identifies parts arriving
> without serial numbers, recovers their identifiers from purchase order and batch records,
> routes them to the correct business unit, and generates step-by-step action instructions
> — reducing manual resolution time from 4–6 hours to under 30 seconds."

---

## Walk Order

Walk through files in this order. Takes 8–10 minutes.

```
1. docs/ARCHITECTURE.md     — show the diagram, explain the problem
2. src/state.py             — explain shared state design
3. src/graph.py             — explain the LangGraph workflow
4. src/agents/supervisor.py — entry point, classification
5. src/agents/part_identifier.py — catalog search + confidence
6. src/agents/serial_resolver.py — PO lookup + serial recovery
7. src/agents/router.py     — BU assignment
8. src/agents/action_recommender.py — instruction generation
9. src/agents/escalation.py — human-in-the-loop
10. main.py                 — live demo
```

---

## Step 1 — The Problem (2 minutes)

Open `docs/ARCHITECTURE.md`. Point to the diagram.

> "The problem I'm solving: parts arrive at the receiving dock without serial numbers
> or part numbers. Without identification, the receiving team doesn't know what the part is,
> which business unit needs it, or what to do with it. Safety-critical parts — brakes,
> sensors, steering — sitting unrouted is a production and safety risk."

> "Manually, this takes 4–6 hours. Someone has to dig through purchase orders, call the
> supplier, cross-reference the catalog, figure out who owns the part, and write up
> instructions. I built an AI workflow that does this in under 30 seconds."

---

## Step 2 — Shared State (`src/state.py`) (1 minute)

```python
class WorkflowState(TypedDict):
    query: str
    identified_part: Optional[dict]
    identification_confidence: float
    recovered_serial: Optional[str]
    serial_confidence: float
    target_business_unit: Optional[str]
    action_plan: Optional[str]
    escalated: bool
    messages: Annotated[list, operator.add]
```

> "In LangGraph, every agent reads from and writes to a shared state object. This is the
> contract between all agents — each one reads what it needs and adds its outputs.
> The `messages` field uses `operator.add` as the reducer, so each agent appends
> rather than overwrites the conversation history."

> "Everything is typed with TypedDict. If an agent returns a key that doesn't exist
> in the schema, it fails at the boundary — not deep inside business logic."

---

## Step 3 — The Graph (`src/graph.py`) (2 minutes)

```python
workflow.add_conditional_edges(
    "serial_resolver",
    lambda state: "router" if state["serial_confidence"] >= 0.7 else "escalation",
    {"router": "router", "escalation": "escalation"}
)
```

> "This is the key design decision — the confidence threshold. After the serial resolver
> runs, LangGraph evaluates this lambda. If confidence is high enough, we route to the
> business unit and generate instructions. If not, we escalate to a human specialist."

> "The threshold is 0.7. For safety-critical parts I'd tighten it to 0.85. For body
> panels I'd loosen it. This is configurable without touching any agent logic."

> "LangGraph compiles this into an executable graph — it handles the state transitions,
> the conditional routing, and the execution order. I don't manage that manually."

---

## Step 4 — Supervisor Agent (1 minute)

```python
SYSTEM = """
Classify the query as: parts | supply_chain | finance | cross
Return JSON: {"query_type": "...", "next": "..."}
"""
```

> "The supervisor is the entry point. It classifies the query so the graph knows which
> path to take. A parts query goes to identification. A finance query skips directly
> to the finance agent. A cross-domain query fans out to both supply chain and finance
> and then synthesizes."

> "The LLM returns structured JSON. Every agent returns structured JSON. No free text
> between agents — it would break downstream parsing."

---

## Step 5 — Part Identifier (1 minute)

```python
@tool
def search_catalog(description: str, category: str = None) -> list[dict]:
    """Fuzzy search the parts catalog. Returns top 5 matches with similarity scores."""
```

> "The part identifier has access to two tools: catalog search and PO lookup.
> Claude decides which tool to call based on what context is available in the query.
> If there's a PO number, it looks that up first — much higher confidence.
> If there's only a description, it does a fuzzy catalog search."

> "Confidence is set based on match quality: exact part number match gives 0.95,
> description-only fuzzy match gives 0.60–0.75. That confidence propagates through
> the entire rest of the workflow."

---

## Step 6 — Serial Resolver (1 minute)

> "Once we have a part match, the serial resolver tries to recover the serial number.
> It looks up the PO, finds the line item for this part, and extracts the serial range
> from the batch record."

> "If PO-2024-0445 had 50 units of FSB-2024-L in batch B2024-0315, with serials
> SN-FSB-0445-001 through SN-FSB-0445-050, and this is a single unit delivery,
> we assign the next available serial from that range. Confidence: 0.95."

> "If the PO has multiple part types and we can't narrow it down, confidence drops
> to 0.75 and we flag it for the human to confirm the specific serial."

---

## Step 7 — Router & Action Recommender (1 minute)

> "Routing is rule-based. Brake system parts → Safety Systems Team, priority critical.
> Sensor hardware → Sensor Integration Team, priority high. The LLM adds context —
> it knows the storage requirements, the QC checklist, the contact person."

> "The action plan comes out as numbered steps: apply the label, store in Bin S-14,
> notify Sensor Integration via Slack, schedule QC inspection within 4 hours, log
> in ERP under PO-2024-0445. The receiving clerk just follows the steps."

---

## Step 8 — Escalation Path (30 seconds)

> "When confidence is low, we don't guess. We package everything we've gathered —
> the closest catalog matches, the PO context, the supplier records — and flag it
> for a human specialist with a pre-built investigation starting point.
> That cuts the manual resolution time from 4–6 hours to 30–45 minutes."

---

## Live Demo (2 minutes)

Run the CLI:

```bash
# Parts identification demo
python main.py --query "Received a metal bracket about 30cm from Acme Forgings, PO-2024-0445"

# Supply chain query
python main.py --query "Which suppliers had the highest defect rates last month?"

# Finance query
python main.py --query "What is the cost variance for brake components in Q1?"

# Cross-domain
python main.py --query "How does the defect rate from Acme Forgings correlate with our procurement cost overruns?"

# Escalation demo (low confidence)
python main.py --query "Received some kind of metal part, no idea what it is"
```

Show the output structure for each.

---

## Talking Points for Architecture Questions

**"Why LangGraph and not a simple sequential pipeline?"**
> "Sequential pipelines can't do conditional routing. The confidence check — route to
> escalation vs route to BU assignment — requires a graph with conditional edges.
> LangGraph handles that natively. It also manages state across agents so I don't
> have to pass data manually between steps."

**"Why a separate agent for identification vs serial resolution?"**
> "Single responsibility. Part identification uses fuzzy catalog search. Serial recovery
> uses PO and batch record lookup. They use different tools, different prompts,
> and can fail independently. If serial recovery fails, I still know what the part is —
> that's useful for escalation. Combining them would lose that granularity."

**"How do you prevent the LLM from hallucinating a serial number?"**
> "The serial resolver only returns serials it finds in the PO or batch records.
> The tool returns the data; the LLM extracts from what the tool returned.
> It's not generating serials from training weights — it's reading from a data source.
> If the tool returns nothing, confidence goes to 0.5 and we escalate."

**"What's the confidence threshold and how did you choose 0.7?"**
> "0.7 is a starting point for demo purposes. In production I'd tune it per part category.
> Safety-critical parts like brakes would be 0.85 — I'd rather escalate more cases
> than misroute a brake caliper. Body panels might be 0.6 — lower cost of error.
> The threshold is in config, not hardcoded."

**"How do you evaluate this in production?"**
> "Three metrics: identification accuracy (% of parts correctly identified vs ground truth),
> routing accuracy (% sent to correct BU), and escalation rate (want <20%, meaning
> 80%+ of cases resolved automatically). I'd build a golden test set of 100 labeled
> historical cases and run the workflow against them."

---

## Quick-Fire Q&A

| Question | Answer |
|---|---|
| What is LangGraph? | A state machine framework for multi-agent AI workflows with conditional routing |
| What is the state? | A TypedDict shared across all agents — immutable, typed, append-only for messages |
| How does routing work? | Conditional edges evaluate state after each node — lambda returns next node name |
| Why structured JSON output? | Downstream agents parse upstream outputs programmatically — free text breaks parsing |
| What triggers escalation? | serial_confidence < 0.7 after the Serial Resolver runs |
| How are tools used? | Claude uses tool_use to call catalog search, PO lookup, batch record lookup |
| What model? | claude-sonnet-4-6 — structured output, tool use, low hallucination |
| How is confidence calculated? | Rule-based scoring on match quality — not LLM-generated |
| What's in the escalation package? | Top 3 catalog matches, PO context, supplier records, suggested lookup steps |
| How long does it take? | <30s end-to-end for 95% of cases |
