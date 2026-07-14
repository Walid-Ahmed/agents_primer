# What this file does: publishes a live-weather tool from a local MCP server.
"""Local MCP server that exposes one live-weather tool over stdio.

This process does not call a language model. It publishes a standard MCP tool
that any compatible MCP client can discover and call.

Do not print debugging text to stdout: stdio MCP uses stdout for protocol data.
"""

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from mcp.server.fastmcp import FastMCP


# FastMCP derives the tool's JSON schema from Python type hints and its docstring.
mcp = FastMCP("Local Weather MCP Server")


def get_json(url: str, params: dict) -> dict:
    """Send a small HTTP GET request and parse the JSON response."""
    request_url = f"{url}?{urlencode(params)}"
    with urlopen(request_url, timeout=10) as response:
        return json.load(response)


@mcp.tool()
def get_current_weather(city: str) -> str:
    """Get live current weather for a city using Open-Meteo."""
    # First resolve the city name to latitude and longitude.
    places = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = places.get("results", [])
    if not results:
        return json.dumps({"error": f"City not found: {city}"})

    place = results[0]

    # Then request current conditions for those coordinates.
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

    return json.dumps(
        {
            "location": f"{place['name']}, {place.get('country', '')}".strip(", "),
            "current": forecast["current"],
            "units": forecast["current_units"],
        }
    )


if __name__ == "__main__":
    # stdio keeps this server local. The agent starts and stops the process.
    mcp.run(transport="stdio")
