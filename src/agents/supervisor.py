from src.state import WorkflowState
from src.agents.llm import call_llm, extract_json

SYSTEM = """
You are the AI supervisor for supply chain and finance operations.
Classify the incoming query and extract key information.

Query types:
- "parts": part identification, missing serial numbers, part number recovery, routing unidentified parts
- "supply_chain": supplier performance, defect rates, lead times, delivery metrics
- "finance": cost variance, reconciliation, budget vs actuals, unreconciled items
- "cross": requires both supply chain and finance data to answer

For "parts" queries, extract:
- part_description: what the part looks like or any identifying details
- shipment_context: any PO numbers, supplier names, dates, quantities mentioned

Return ONLY valid JSON in this exact format:
{
  "query_type": "parts|supply_chain|finance|cross",
  "part_description": "extracted description or empty string",
  "shipment_context": {
    "po_number": "PO-XXXX-XXXX or null",
    "supplier_name": "supplier name or null",
    "quantity": null or number,
    "date": "date or null"
  },
  "next": "part_identifier|supply_chain|finance|cross",
  "reasoning": "one sentence explanation"
}
"""


def run(state: WorkflowState) -> dict:
    response = call_llm(
        system=SYSTEM,
        user=f"Query: {state['query']}",
    )

    text = response.content[0].text
    parsed = extract_json(text)

    return {
        "query_type": parsed.get("query_type", "parts"),
        "part_description": parsed.get("part_description", state["query"]),
        "shipment_context": parsed.get("shipment_context", {}),
        "next": parsed.get("next", "part_identifier"),
        "messages": [{"role": "supervisor", "content": parsed.get("reasoning", "")}],
    }
