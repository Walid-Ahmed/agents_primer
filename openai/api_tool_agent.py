# What this file does: lets an OpenAI agent call a live weather API tool.
"""Minimal agent whose tool calls a real external weather API.

Run from the repository root:
    python openai/api_tool_agent.py
    python openai/api_tool_agent.py "Mexico City"

Two different APIs are involved:
1. This application calls the OpenAI Responses API to ask the model what to do.
2. The selected Python tool calls Open-Meteo to obtain current external data.

Concept map:
- Tool calling: YES. The weather API is exposed to the model as a function tool.
- External API: YES. Python—not the model—sends the HTTP requests to Open-Meteo.
- ReAct: ONE-ROUND ReAct-style flow: decide, act, observe, then answer.
- Chain-of-Thought: NO. Visible step-by-step reasoning is not requested.
- Reasoning tokens: NOT CONFIGURED OR INSPECTED.
"""

import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv
from openai import OpenAI


def get_json(url: str, params: dict) -> dict:
    """Make a small GET request and parse its JSON response."""
    request_url = f"{url}?{urlencode(params)}"
    # A timeout prevents an unavailable service from hanging the agent forever.
    with urlopen(request_url, timeout=10) as response:
        return json.load(response)


def get_current_weather(city: str) -> str:
    """Resolve a city to coordinates, then retrieve its current weather."""
    # External API call 1: translate the model-provided city into coordinates.
    places = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = places.get("results", [])
    if not results:
        return json.dumps({"error": f"City not found: {city}"})

    place = results[0]

    # External API call 2: request current conditions for those coordinates.
    forecast = get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": (
                "temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
            ),
            "timezone": "auto",
        },
    )

    # Return only useful fields. Smaller tool results reduce model input cost.
    return json.dumps(
        {
            "location": f"{place['name']}, {place.get('country', '')}".strip(", "),
            "current": forecast["current"],
            "units": forecast["current_units"],
        }
    )


WEATHER_TOOL = {
    "type": "function",
    "name": "get_current_weather",
    "description": "Get live current weather for a city using Open-Meteo.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, optionally including country or region",
            }
        },
        "required": ["city"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Add OPENAI_API_KEY to a .env file")

    city = sys.argv[1] if len(sys.argv) > 1 else "Toronto"
    client = OpenAI()

    # Model API call 1: let the model decide whether to request the tool.
    response = client.responses.create(
        model="gpt-5-nano",
        input=f"What is the current weather in {city}? Use the weather tool.",
        tools=[WEATHER_TOOL],
    )

    calls = [item for item in response.output if item.type == "function_call"]
    if not calls:
        print(response.output_text)
        return

    outputs = []
    for call in calls:
        arguments = json.loads(call.arguments)
        result = get_current_weather(arguments["city"])
        print(f"TOOL: {call.name}({arguments})")
        print(f"EXTERNAL API RESULT: {result}")
        outputs.append(
            {
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": result,
            }
        )

    # Model API call 2: give the external API result back for a natural answer.
    final_response = client.responses.create(
        model="gpt-5-nano",
        previous_response_id=response.id,
        input=outputs,
        tools=[WEATHER_TOOL],
    )
    print(f"\nFINAL ANSWER: {final_response.output_text}")


if __name__ == "__main__":
    main()
