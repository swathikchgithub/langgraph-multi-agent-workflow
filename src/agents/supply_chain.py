from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools, extract_json
from src.tools.catalog_tools import SUPPLY_CHAIN_TOOLS, dispatch_tool

SYSTEM = """
You are a supply chain analyst. Answer questions about supplier performance,
defect rates, lead times, delivery metrics, and purchase order history.

Use the available tools to look up current data, then provide a clear analysis.

Be specific: include numbers, percentages, dates, and trends.
Flag any suppliers with defect rates above 3% or on-time delivery below 90%.

After gathering data, respond with a natural language answer that a supply chain
manager would find actionable. Include a brief data summary and specific recommendations.
"""


def run(state: WorkflowState) -> dict:
    final_text, tool_log = call_llm_with_tools(
        system=SYSTEM,
        user=state["query"],
        tools=SUPPLY_CHAIN_TOOLS,
        dispatch_fn=dispatch_tool,
    )

    return {
        "supply_chain_answer": final_text,
        "messages": [
            {"role": "supply_chain", "content": final_text},
            *[{"role": "tool_call", "content": str(t)} for t in tool_log],
        ],
    }
