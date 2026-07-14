# What this file does: demonstrates a multi-round OpenAI tool loop.
"""Minimal multi-round tool loop using OpenAI's Responses API.

Run from the repository root:
    python openai/tool_loop.py

The task needs two dependent tools:
1. Find Alice's city.
2. Use that returned city to get its weather.

Because the second call depends on the first result, the application uses a
bounded while loop instead of assuming one tool-call round will be enough.

Concept map:
- Tool calling: YES. The model requests structured function calls.
- ReAct: YES, in the modern "ReAct-style" sense. The runtime repeatedly lets the
  model decide, executes its action, returns an observation, and continues.
- Chain-of-Thought (CoT): NO. We do not ask for or expose step-by-step reasoning.
- Reasoning tokens: NOT CONFIGURED OR INSPECTED. They are separate from the loop.

Modern APIs do not need literal "Thought / Action / Observation" text. Structured
function calls are the actions, function outputs are the observations, and the
model's private reasoning does not need to be shown.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# These fake tools keep the lesson focused on orchestration, not external APIs.
def get_user_city(user_name: str) -> str:
    """Look up a user's city."""
    cities = {"alice": "Toronto", "bob": "Vancouver"}
    return cities.get(user_name.lower(), "Unknown")


def get_weather(city: str) -> str:
    """Look up weather for a city."""
    weather = {"toronto": "18 C and sunny", "vancouver": "14 C and rainy"}
    return weather.get(city.lower(), "Weather unavailable")


TOOLS = [
    {
        "type": "function",
        "name": "get_user_city",
        "description": "Look up the city where a user lives.",
        "parameters": {
            "type": "object",
            "properties": {"user_name": {"type": "string"}},
            "required": ["user_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather for a known city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    """Route a validated model request to the matching Python function."""
    if name == "get_user_city":
        return get_user_city(arguments["user_name"])
    if name == "get_weather":
        return get_weather(arguments["city"])
    raise ValueError(f"Unknown tool: {name}")


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Add OPENAI_API_KEY to a .env file")

    client = OpenAI()
    response = client.responses.create(
        model="gpt-5-nano",
        input=(
            "What weather should Alice prepare for? First use get_user_city. "
            "Use only the returned city when calling get_weather."
        ),
        tools=TOOLS,
    )

    # A limit prevents bugs or model behavior from creating an infinite loop.
    max_tool_rounds = 5
    tool_round = 0

    while tool_round < max_tool_rounds:
        calls = [item for item in response.output if item.type == "function_call"]

        # No calls means the model has finished and returned its final answer.
        if not calls:
            print(f"\nFINAL ANSWER: {response.output_text}")
            return

        tool_round += 1
        print(f"\nTOOL ROUND {tool_round}")
        outputs = []

        # One round can contain one call or several independent parallel calls.
        for call in calls:
            arguments = json.loads(call.arguments)
            result = execute_tool(call.name, arguments)
            print(f"{call.name}({arguments}) -> {result}")

            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": result,
                }
            )

        # Continue from the previous response. The model sees the tool results and
        # can answer, request the next dependent tool, or request several tools.
        response = client.responses.create(
            model="gpt-5-nano",
            previous_response_id=response.id,
            input=outputs,
            tools=TOOLS,
        )

    raise RuntimeError(f"Agent exceeded the limit of {max_tool_rounds} tool rounds")


if __name__ == "__main__":
    main()
