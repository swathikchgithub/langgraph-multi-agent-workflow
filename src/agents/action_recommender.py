from src.state import WorkflowState
from src.agents.llm import call_llm, extract_json

SYSTEM = """
You are a operations specialist who writes clear action plans for warehouse and
receiving teams dealing with identified parts.

Given all available information about a part — its identity, recovered serial number,
routing assignment, and QC requirements — write a concrete step-by-step action plan
for the receiving team.

The action plan must be practical, specific, and actionable. Include:
1. Immediate labeling steps (what labels to apply, what numbers to use)
2. Physical handling instructions (storage location, orientation, temperature if relevant)
3. QC steps if required
4. Notification steps (who to contact, what to tell them)
5. System entry steps (what to log in the ERP/inventory system)

Respond with JSON:
{
  "action_plan": "Full multi-step action plan as a numbered list",
  "immediate_actions": ["action1", "action2"],
  "estimated_time_minutes": 15,
  "requires_specialist": false,
  "warnings": []
}
"""


def run(state: WorkflowState) -> dict:
    identified = state.get("identified_part") or {}
    context = {
        "part_number": identified.get("part_number", "UNKNOWN"),
        "part_name": identified.get("part_name", state["part_description"]),
        "category": identified.get("category", "unknown"),
        "recovered_serial": state.get("recovered_serial"),
        "recovered_part_number": state.get("recovered_part_number"),
        "target_business_unit": state.get("target_business_unit"),
        "priority": state.get("priority", "normal"),
        "contact_person": state.get("contact_person"),
        "storage_location": state.get("storage_location"),
        "qc_required": state.get("qc_required", False),
        "identification_confidence": state.get("identification_confidence", 0.0),
        "serial_confidence": state.get("serial_confidence", 0.0),
    }

    user_msg = f"""
Part identified: {context['part_number']} — {context['part_name']}
Category: {context['category']}
Recovered serial: {context['recovered_serial'] or 'Could not recover'}
Recovered part number: {context['recovered_part_number'] or 'Could not recover'}
Assigned BU: {context['target_business_unit']}
Priority: {context['priority']}
Contact: {context['contact_person']}
Storage: {context['storage_location']}
QC required: {context['qc_required']}
ID confidence: {context['identification_confidence']:.0%}
Serial confidence: {context['serial_confidence']:.0%}

Write the action plan for the receiving team.
"""

    response = call_llm(system=SYSTEM, user=user_msg)
    text = response.content[0].text

    try:
        parsed = extract_json(text)
    except Exception:
        parsed = {"action_plan": text}

    return {
        "action_plan": parsed.get("action_plan", text),
        "messages": [{"role": "action_recommender", "content": parsed.get("action_plan", text)}],
    }
