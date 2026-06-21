import json
import os
from anthropic import Anthropic

_client = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def call_llm(system: str, user: str, tools: list = None) -> dict:
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if tools:
        kwargs["tools"] = tools

    response = get_client().messages.create(**kwargs)
    return response


def call_llm_with_tools(system: str, user: str, tools: list, dispatch_fn) -> tuple[str, list]:
    """
    Runs an agentic loop: calls LLM, dispatches tool calls, feeds results back,
    continues until the LLM produces a final text response.
    Returns (final_text, tool_call_log).
    """
    messages = [{"role": "user", "content": user}]
    tool_log = []

    while True:
        response = get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=tools,
        )

        # Collect tool uses
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if response.stop_reason == "end_turn" or not tool_uses:
            final_text = text_blocks[0].text if text_blocks else ""
            return final_text, tool_log

        # Append assistant message
        messages.append({"role": "assistant", "content": response.content})

        # Dispatch each tool call and collect results
        tool_results = []
        for tool_use in tool_uses:
            result = dispatch_fn(tool_use.name, tool_use.input)
            tool_log.append({"tool": tool_use.name, "input": tool_use.input, "result": result})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})


def extract_json(text: str) -> dict:
    """Extract JSON from LLM text response, handling markdown code blocks."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)
