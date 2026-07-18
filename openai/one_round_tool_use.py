# What this file does: demonstrates one round of OpenAI function calling.
"""Minimal OpenAI function-calling example with one tool-call round.

Run from the repository root:
    python openai/one_round_tool_use.py

Registering a function makes it available to the model. It does not guarantee
that the model will call it; the prompt and tool description guide that choice.

This beginner example handles every function call in the first response, but it
does not loop if the model requests another function after seeing those results.
See multi_round_tool_loop.py for a bounded while-loop that supports multiple rounds.

Concept map:
- Tool calling: YES. This is the main concept demonstrated here.
- ReAct: NOT YET. A full ReAct-style agent must repeat tool-call rounds.
- Chain-of-Thought (CoT): NO. The prompt does not request visible steps.
- Reasoning tokens: NOT CONFIGURED OR INSPECTED in this lesson.
"""

import json
import os
from typing import TextIO

from dotenv import load_dotenv
from openai import OpenAI
from logging_utils import execution_log, log_message


# 1. This function runs in our application, not inside the model.
def get_weather(city: str) -> str:
    """Return fake weather so the lesson does not need another API key."""
    weather_by_city = {
        "toronto": "18 C and sunny",
        "vancouver": "14 C and rainy",
    }
    return weather_by_city.get(city.lower(), "Weather is unavailable for that city")


# 2. Register the function's interface with the model.
# The model sees this schema, but it does not see the Python implementation above.
TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, for example Toronto",
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


# Compare prompts that need the tool, do not need it, and prohibit it.
PROMPTS = [
    "What is the weather in Toronto?",
    "What is the capital of Canada?",
    "Without using any tools, guess what Toronto's weather is like.",
]


def run_prompt(client: OpenAI, prompt: str, log_file: TextIO) -> None:
    """Ask the model, report function calls, then complete the tool-use loop."""
    log_message(log_file, "User input", prompt)

    response = client.responses.create(
        # GPT-5 nano is the cheapest GPT-5 model and supports function calling.
        model="gpt-5-nano",
        input=prompt,
        tools=TOOLS,  # Makes get_weather available to the model.
        # tool_choice defaults to "auto": zero or more calls are allowed.
    )
    log_message(log_file, "Model response", response.model_dump())

    # 3. Check structured output items. Do not infer tool use from response text.
    function_calls = [
        item for item in response.output if item.type == "function_call"
    ]

    print(f"\nPROMPT: {prompt}")
    print(f"USED A TOOL: {bool(function_calls)}")

    if not function_calls:
        print(f"ANSWER: {response.output_text}")
        return

    # 4. Execute every function requested by the model.
    function_outputs = []
    for call in function_calls:
        arguments = json.loads(call.arguments)
        print(f"FUNCTION CALL: {call.name}({arguments})")

        if call.name == "get_weather":
            result = get_weather(arguments["city"])
        else:
            result = f"Unknown function: {call.name}"

        function_outputs.append(
            {
                # This type identifies a structured API result, not a human speaker.
                # call_id links this result to the exact function call the model requested.
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": result,
            }
        )

    log_message(log_file, "Function outputs returned to model", function_outputs)

    # 5. Continue the same response with the results from our application.
    # This is one round only. A full agent must inspect final_response for more
    # function_call items and keep looping until it receives a final answer.
    final_response = client.responses.create(
        model="gpt-5-nano",
        previous_response_id=response.id,
        input=function_outputs,
        tools=TOOLS,
    )
    log_message(log_file, "Model final response", final_response.model_dump())

    print(f"TOOL RESULT: {function_outputs[0]['output']}")
    print(f"FINAL ANSWER: {final_response.output_text}")


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Add OPENAI_API_KEY to a .env file")

    client = OpenAI()

    # The helper creates openai/logs/, opens a timestamped file, closes it at
    # the end of the with block, and prints the full log path.
    with execution_log(__file__) as log_file:
        for prompt in PROMPTS:
            run_prompt(client, prompt, log_file)


if __name__ == "__main__":
    main()
