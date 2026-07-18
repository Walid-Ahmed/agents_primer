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


# Create the MCP server. The name helps clients identify it during connection.
# FastMCP derives each tool's JSON schema from Python type hints and docstrings.
mcp = FastMCP("Local Weather MCP Server")


def get_json(url: str, params: dict) -> dict:
    """Send a small HTTP GET request and parse the JSON response."""
    # Convert the parameters into a URL query string such as name=Toronto&count=1.
    request_url = f"{url}?{urlencode(params)}"
    # The timeout prevents a slow external service from hanging the MCP call.
    with urlopen(request_url, timeout=10) as response:
        # Convert the JSON response body into a Python dictionary.
        return json.load(response)


# This decorator registers the Python function as an MCP tool. It does not call
# the function now; it makes the tool discoverable to a connected MCP client.
@mcp.tool()
def get_current_weather(city: str) -> str:
    """Get live current weather for a city using Open-Meteo."""
    # First resolve the city name to latitude and longitude.
    places = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = places.get("results", [])
    # Return a useful tool result instead of raising an error for an unknown city.
    if not results:
        return json.dumps({"error": f"City not found: {city}"})

    # count=1 requested only the best matching location.
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

    # Return JSON text because it preserves the structure for the agent while
    # keeping the MCP tool's return type simple (`str`).
    return json.dumps(
        {
            "location": f"{place['name']}, {place.get('country', '')}".strip(", "),
            "current": forecast["current"],
            "units": forecast["current_units"],
        }
    )


if __name__ == "__main__":
    # This runs only when the file is started as a program, not when imported.
    # stdio means the agent and server exchange MCP protocol messages through
    # stdin/stdout. The agent starts and stops this local subprocess.
    # Never use print() here: ordinary stdout text would corrupt the protocol.
    mcp.run(transport="stdio")
