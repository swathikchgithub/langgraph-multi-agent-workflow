from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools
from src.tools.catalog_tools import CATALOG_TOOLS, dispatch_tool

SYSTEM = """
You are a parts identification specialist. Your job is to identify unknown parts
arriving without serial or part numbers.

Given a description of a part, use the search_catalog tool to find matches.
If the part has a PO number or supplier info, use lookup_po or lookup_by_supplier
to recover the original part numbers and serial ranges.

After tool calls, respond with a JSON object:
{
  "identified_part": {
    "part_number": "...",
    "part_name": "...",
    "category": "...",
    "description": "...",
    "weight_kg": ...,
    "compatible_models": [...]
  },
  "identification_confidence": 0.0-1.0,
  "identification_source": "catalog_match|po_lookup|supplier_lookup|combined",
  "reasoning": "brief explanation of how you identified the part"
}

If you cannot identify the part with confidence >= 0.5, set identified_part to null
and explain in reasoning.
"""


def run(state: WorkflowState) -> dict:
    context_parts = [f"Part description: {state['part_description']}"]
    ctx = state.get("shipment_context", {})
    if ctx.get("po_number"):
        context_parts.append(f"PO number: {ctx['po_number']}")
    if ctx.get("supplier_name"):
        context_parts.append(f"Supplier: {ctx['supplier_name']}")
    if ctx.get("quantity"):
        context_parts.append(f"Quantity: {ctx['quantity']}")

    user_msg = "\n".join(context_parts)

    final_text, tool_log = call_llm_with_tools(
        system=SYSTEM,
        user=user_msg,
        tools=CATALOG_TOOLS,
        dispatch_fn=dispatch_tool,
    )

    try:
        from src.agents.llm import extract_json
        parsed = extract_json(final_text)
    except Exception:
        parsed = {}

    identified = parsed.get("identified_part")
    confidence = float(parsed.get("identification_confidence", 0.0))

    return {
        "identified_part": identified,
        "identification_confidence": confidence,
        "identification_source": parsed.get("identification_source", "unknown"),
        "messages": [
            {"role": "part_identifier", "content": parsed.get("reasoning", final_text)},
            *[{"role": "tool_call", "content": str(t)} for t in tool_log],
        ],
    }
