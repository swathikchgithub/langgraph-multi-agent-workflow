from src.state import WorkflowState
from src.agents.llm import call_llm

SYSTEM = """
You are a operations synthesizer. Combine answers from multiple specialized agents
into a single, coherent, executive-level summary.

Format the response clearly with:
- A one-paragraph executive summary
- Specific findings from each domain that was queried
- Clear action items with owners and priority

Be concise but complete. A manager should be able to act on your response immediately.
"""


def run(state: WorkflowState) -> dict:
    parts = [f"Original query: {state['query']}"]

    if state.get("supply_chain_answer"):
        parts.append(f"\n## Supply Chain Analysis\n{state['supply_chain_answer']}")

    if state.get("finance_answer"):
        parts.append(f"\n## Finance Analysis\n{state['finance_answer']}")

    if state.get("action_plan"):
        parts.append(f"\n## Parts Handling Action Plan\n{state['action_plan']}")

    if state.get("escalated"):
        parts.append(f"\n## Escalation Required\n{state.get('escalation_reason', '')}")

    user_msg = "\n".join(parts) + "\n\nSynthesize these findings into a unified response."

    response = call_llm(system=SYSTEM, user=user_msg)
    final_answer = response.content[0].text

    return {
        "final_answer": final_answer,
        "messages": [{"role": "synthesizer", "content": final_answer}],
    }
