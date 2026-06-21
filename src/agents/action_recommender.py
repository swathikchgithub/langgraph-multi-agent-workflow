from src.state import WorkflowState
from src.agents.llm import call_llm

SYSTEM = """
You are an operations specialist who writes clear action plans for warehouse and
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

Write as plain numbered text. Do not use JSON or markdown code blocks.
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
    action_plan = response.content[0].text.strip()

    return {
        "action_plan": action_plan,
        "messages": [{"role": "action_recommender", "content": action_plan}],
    }
