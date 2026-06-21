import json
from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools, extract_json
from src.tools.catalog_tools import get_business_unit_info

SYSTEM = """
You are a parts routing specialist. You assign identified parts to the correct
business unit and determine handling instructions.

Given an identified part with its category, use get_business_unit_info to determine:
- Which business unit receives the part
- Priority level for processing
- Contact person and Slack channel
- Whether QC inspection is required
- Storage location in the warehouse

After calling the tool, respond with JSON only — no markdown, no explanation:
{
  "target_business_unit": "...",
  "priority": "critical|high|normal|low",
  "contact_person": "...",
  "storage_location": "...",
  "qc_required": true|false,
  "slack_channel": "..."
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

    tool_results = {}

    def dispatch(name, inp):
        if name == "get_business_unit_info":
            result = get_business_unit_info(**inp)
            tool_results.update(json.loads(result))
            return result
        return "{}"

    final_text, _ = call_llm_with_tools(
        system=SYSTEM,
        user=user_msg,
        tools=ROUTING_TOOL,
        dispatch_fn=dispatch,
    )

    try:
        parsed = extract_json(final_text)
    except Exception:
        parsed = {}

    # Fall back to raw tool results if JSON parsing failed
    def get(key, default=None):
        return parsed.get(key) or tool_results.get(key, default)

    return {
        "target_business_unit": get("target_business_unit") or get("business_unit"),
        "priority": get("priority", "normal"),
        "contact_person": get("contact_person"),
        "storage_location": get("storage_location") or tool_results.get("storage_area"),
        "qc_required": bool(get("qc_required", False)),
        "messages": [{"role": "router", "content": final_text}],
    }
