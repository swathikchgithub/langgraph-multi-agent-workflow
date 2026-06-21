from src.state import WorkflowState
from src.agents.llm import call_llm_with_tools
from src.tools.catalog_tools import FINANCE_TOOLS, dispatch_tool

SYSTEM = """
You are a finance analyst specializing in procurement and parts spend.
Answer questions about cost variance, budget vs actuals, unreconciled items,
and supplier spend analysis.

Use the available tools to get current data, then provide a clear financial analysis.

Be precise: include dollar amounts, percentages, and variance directions (over/under budget).
Flag any category with variance > 10% or unreconciled items older than 30 days.

Respond with a clear, actionable financial summary that a procurement manager
would use to prioritize follow-up actions.
"""


def run(state: WorkflowState) -> dict:
    final_text, tool_log = call_llm_with_tools(
        system=SYSTEM,
        user=state["query"],
        tools=FINANCE_TOOLS,
        dispatch_fn=dispatch_tool,
    )

    return {
        "finance_answer": final_text,
        "messages": [
            {"role": "finance", "content": final_text},
            *[{"role": "tool_call", "content": str(t)} for t in tool_log],
        ],
    }
