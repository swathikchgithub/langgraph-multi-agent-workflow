from src.state import WorkflowState
from src.agents.llm import call_llm, extract_json

SYSTEM = """
You are an escalation specialist. A part has arrived that could not be identified
with sufficient confidence, or could not have its serial number recovered.

Your job is to:
1. Summarize what is known about the part
2. Explain why automated processing cannot continue
3. Create an investigation package for a human specialist
4. Recommend immediate safe handling (quarantine location, labeling)
5. Identify who needs to be notified

Respond with JSON:
{
  "escalation_reason": "clear explanation of why this needs human review",
  "investigation_package": {
    "part_description": "...",
    "what_was_tried": ["search_catalog", "po_lookup", ...],
    "best_guess": "part it most closely resembles, if any",
    "best_guess_confidence": 0.0-1.0,
    "po_context": "any PO info we have",
    "recommended_specialist": "who should investigate (e.g. Supplier Quality Engineer)",
    "quarantine_location": "Zone Q / Shelf Q-1",
    "temp_label": "UNIDENTIFIED-YYYYMMDD-XXXX"
  },
  "notifications": [
    {"team": "Receiving Manager", "message": "brief message"},
    {"team": "Supplier Quality", "message": "brief message"}
  ]
}
"""


def run(state: WorkflowState) -> dict:
    identified = state.get("identified_part") or {}
    context = {
        "query": state["query"],
        "part_description": state["part_description"],
        "identification_confidence": state.get("identification_confidence", 0.0),
        "serial_confidence": state.get("serial_confidence", 0.0),
        "identified_part": identified,
        "shipment_context": state.get("shipment_context", {}),
    }

    reasons = []
    if context["identification_confidence"] < 0.7:
        reasons.append(
            f"Part identification confidence too low: {context['identification_confidence']:.0%} (threshold: 70%)"
        )
    if context["serial_confidence"] < 0.7:
        reasons.append(
            f"Serial number recovery confidence too low: {context['serial_confidence']:.0%} (threshold: 70%)"
        )

    user_msg = f"""
Escalation triggers: {'; '.join(reasons) if reasons else 'Manual escalation requested'}

Part description: {context['part_description']}
Identification attempt: {identified.get('part_name', 'No match found')} at {context['identification_confidence']:.0%} confidence
PO context: {context['shipment_context']}
Original query: {context['query']}

Create the escalation package.
"""

    response = call_llm(system=SYSTEM, user=user_msg)
    text = response.content[0].text

    try:
        parsed = extract_json(text)
    except Exception:
        parsed = {"escalation_reason": text, "investigation_package": {}}

    return {
        "escalated": True,
        "escalation_reason": parsed.get("escalation_reason", "; ".join(reasons)),
        "investigation_package": parsed.get("investigation_package", {}),
        "messages": [{"role": "escalation", "content": parsed.get("escalation_reason", "")}],
    }
