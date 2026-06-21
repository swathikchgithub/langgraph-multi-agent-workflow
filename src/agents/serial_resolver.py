from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools, extract_json
from src.tools.catalog_tools import CATALOG_TOOLS, dispatch_tool

SYSTEM = """
You are a serial number and part number recovery specialist.
A part has arrived without a serial number or part number label.

Your job is to recover the serial number and part number from:
- Purchase order records (use lookup_po with the PO number)
- Supplier shipment records (use lookup_by_supplier)
- Cross-referencing with identified part data

Strategy:
1. If a PO number is known, call lookup_po first — line items contain serial ranges
2. If supplier name is known, call lookup_by_supplier to find relevant POs
3. Cross-reference the identified part_number against PO line items to find serial range

Respond with JSON:
{
  "recovered_serial": "SN-XXXXX or null if not recoverable",
  "recovered_part_number": "PART-NUMBER or null",
  "serial_source": "po_line_item|supplier_batch|inference|not_found",
  "serial_confidence": 0.0-1.0,
  "serial_range": "e.g. SN-10001 to SN-10050 or null",
  "reasoning": "how you recovered these values"
}
"""


def run(state: WorkflowState) -> dict:
    ctx = state.get("shipment_context", {})
    identified = state.get("identified_part") or {}

    context_parts = []
    if identified:
        context_parts.append(f"Identified part: {identified.get('part_number')} — {identified.get('part_name')}")
        context_parts.append(f"Category: {identified.get('category')}")
    if ctx.get("po_number"):
        context_parts.append(f"PO number from shipment: {ctx['po_number']}")
    if ctx.get("supplier_name"):
        context_parts.append(f"Supplier: {ctx['supplier_name']}")
    if not context_parts:
        context_parts.append(f"Part description: {state['part_description']}")

    user_msg = "\n".join(context_parts)

    final_text, tool_log = call_llm_with_tools(
        system=SYSTEM,
        user=user_msg,
        tools=CATALOG_TOOLS,
        dispatch_fn=dispatch_tool,
    )

    try:
        parsed = extract_json(final_text)
    except Exception:
        parsed = {}

    return {
        "recovered_serial": parsed.get("recovered_serial"),
        "recovered_part_number": parsed.get("recovered_part_number"),
        "serial_source": parsed.get("serial_source", "not_found"),
        "serial_confidence": float(parsed.get("serial_confidence", 0.0)),
        "messages": [
            {"role": "serial_resolver", "content": parsed.get("reasoning", final_text)},
            *[{"role": "tool_call", "content": str(t)} for t in tool_log],
        ],
    }
