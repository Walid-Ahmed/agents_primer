# What this file does: demonstrates one round of Anthropic tool calling.
"""Minimal Anthropic tool-use example with one tool-call round.

Run from the repository root:
    python anthropic/one_round_tool_use.py

The important lesson is that registering a tool does not force Claude to use it.
Claude chooses whether to call it based on the prompt and tool description.

This beginner example handles every tool call in Claude's first response, but it
does not loop if Claude asks for another tool after seeing those results. See
openai/multi_round_tool_loop.py for the bounded while-loop pattern used by a real agent.

Concept map:
- Tool calling: YES. This is the main concept demonstrated here.
- ReAct: NOT YET. A full ReAct-style agent must repeat tool-call rounds.
- Chain-of-Thought (CoT): NO. The prompt does not request visible steps.
- Thinking tokens: NO. Extended thinking is not enabled or inspected here.
"""

import os
from typing import TextIO

import anthropic
from dotenv import load_dotenv
from logging_utils import execution_log, log_message


# 1. This is ordinary Python code. Claude cannot run it directly.
def get_weather(city: str) -> str:
    """Return fake weather so this lesson does not need another API key."""
    weather_by_city = {
        "toronto": "18 C and sunny",
        "vancouver": "14 C and rainy",
    }
    return weather_by_city.get(city.lower(), "Weather is unavailable for that city")


# 2. Register the Python function's interface with Claude.
# Claude sees this name, description, and JSON schema—not the function above.
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, for example Toronto",
                }
            },
            "required": ["city"],
        },
    }
]


# Try prompts with different relationships to the registered tool.
PROMPTS = [
    "What is the weather in Toronto?",
    "What is the capital of Canada?",
    "Without using any tools, guess what Toronto's weather is like.",
]


def run_prompt(client: anthropic.Anthropic, prompt: str, log_file: TextIO) -> None:
    """Ask Claude, report whether it called a tool, and finish the turn."""
    messages = [{"role": "user", "content": prompt}]
    log_message(log_file, "User message", prompt)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=TOOLS,  # Passing TOOLS makes the tool available to the model.
        # tool_choice defaults to "auto": Claude may use a tool or answer directly.
        messages=messages,
    )
    log_message(log_file, "Assistant response", response.content)

    # 3. Never infer tool use from prose. Check for structured tool_use blocks.
    tool_calls = [block for block in response.content if block.type == "tool_use"]

    print(f"\nPROMPT: {prompt}")
    print(f"USED A TOOL: {bool(tool_calls)}")
    print(f"STOP REASON: {response.stop_reason}")

    if not tool_calls:
        # A direct answer arrives in the first text block.
        print(f"ANSWER: {response.content[0].text}")
        return

    # 4. Claude requested a tool; our application must execute it.
    tool_results = []
    for call in tool_calls:
        print(f"TOOL CALL: {call.name}({call.input})")

        if call.name == "get_weather":
            result = get_weather(call.input["city"])
        else:
            result = f"Unknown tool: {call.name}"

        tool_results.append(
            {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": result,
            }
        )

    # 5. Send Claude its original response and our tool results.
    # This is one round only. Production agent code should inspect final_response
    # for more tool_use blocks and repeat until Claude returns a final answer.
    messages.append({"role": "assistant", "content": response.content})
    # Anthropic uses the "user" role for tool results because they are input
    # returned to Claude by our application, not because a human sent them.
    messages.append({"role": "user", "content": tool_results})
    log_message(log_file, "Tool results returned as a user message", tool_results)

    final_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=TOOLS,
        messages=messages,
    )
    log_message(log_file, "Assistant final response", final_response.content)
    final_answer = final_response.content[0].text
    print(f"TOOL RESULT: {tool_results[0]['content']}")
    print(f"FINAL ANSWER: {final_answer}")


def main() -> None:
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("Add ANTHROPIC_API_KEY to a .env file")

    client = anthropic.Anthropic()

    # __file__ is the path of this Python script. The helper uses it to create
    # a logs folder beside this file and opens a new timestamped log file.
    # The with block closes the log automatically and then prints its location.
    with execution_log(__file__) as log_file:
        for prompt in PROMPTS:
            run_prompt(client, prompt, log_file)


if __name__ == "__main__":
    main()
