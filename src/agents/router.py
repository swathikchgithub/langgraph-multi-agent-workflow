from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools, extract_json
from src.tools.catalog_tools import CATALOG_TOOLS, dispatch_tool, get_business_unit_info

SYSTEM = """
You are a parts routing specialist. You assign identified parts to the correct
business unit and determine handling instructions.

Given an identified part with its category, use get_business_unit_info to determine:
- Which business unit receives the part
- Priority level for processing
- Contact person and Slack channel
- Whether QC inspection is required
- Storage location in the warehouse

Respond with JSON:
{
  "target_business_unit": "Autonomy Systems|Chassis & Drive|Body & Interiors|Battery Systems|Electrical Systems",
  "priority": "critical|high|normal|low",
  "contact_person": "name and role",
  "storage_location": "warehouse zone and bin",
  "qc_required": true|false,
  "slack_channel": "#channel-name",
  "reasoning": "why this routing was chosen"
}
"""

ROUTING_TOOL = [
    {
        "name": "get_business_unit_info",
        "description": "Get business unit assignment, contact person, storage location, and QC requirements for a part category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "part_category": {
                    "type": "string",
                    "description": "Part category (e.g. sensor_hardware, brake_system, suspension, camera_system, electrical, wiring, body_panels, drive_motor, battery)",
                },
            },
            "required": ["part_category"],
        },
    }
]


def run(state: WorkflowState) -> dict:
    identified = state.get("identified_part") or {}
    category = identified.get("category", "unknown")
    part_number = identified.get("part_number", "unknown")
    part_name = identified.get("part_name", state["part_description"])

    user_msg = f"Route this part:\nPart number: {part_number}\nPart name: {part_name}\nCategory: {category}"

    final_text, tool_log = call_llm_with_tools(
        system=SYSTEM,
        user=user_msg,
        tools=ROUTING_TOOL,
        dispatch_fn=lambda name, inp: get_business_unit_info(**inp) if name == "get_business_unit_info" else "{}",
    )

    try:
        parsed = extract_json(final_text)
    except Exception:
        parsed = {}

    return {
        "target_business_unit": parsed.get("target_business_unit"),
        "priority": parsed.get("priority", "normal"),
        "contact_person": parsed.get("contact_person"),
        "storage_location": parsed.get("storage_location"),
        "qc_required": bool(parsed.get("qc_required", False)),
        "messages": [
            {"role": "router", "content": parsed.get("reasoning", final_text)},
        ],
    }
