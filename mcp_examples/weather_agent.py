"""OpenAI agent that discovers and uses a local weather MCP server.

Run from the repository root:
    python mcp_examples/weather_agent.py
    python mcp_examples/weather_agent.py "Mexico City"

Flow:
1. MCPServerStdio launches weather_server.py as a local subprocess.
2. The agent discovers get_current_weather through the MCP protocol.
3. The model chooses the MCP tool.
4. The server calls Open-Meteo and returns live weather.
5. The Agents SDK completes the tool loop and returns the final answer.

Unlike openai/api_tool_agent.py, this file does not define the tool schema or call
the weather function directly. The MCP server owns and publishes that capability.
"""

import asyncio
import os
import sys
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio, create_static_tool_filter
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Add OPENAI_API_KEY to a .env file")

    city = sys.argv[1] if len(sys.argv) > 1 else "Toronto"
    server_script = Path(__file__).with_name("weather_server.py")

    # The context manager owns the MCP subprocess and closes it automatically.
    async with MCPServerStdio(
        name="Local Weather Server",
        params={
            "command": sys.executable,
            "args": [str(server_script)],
        },
        # Expose only the one tool this lesson intends the agent to use.
        tool_filter=create_static_tool_filter(
            allowed_tool_names=["get_current_weather"]
        ),
        cache_tools_list=True,
    ) as weather_server:
        # Show that tools are discovered from MCP, not declared in this file.
        discovered_tools = await weather_server.list_tools()
        print("MCP TOOLS:", [tool.name for tool in discovered_tools])

        agent = Agent(
            name="Weather Agent",
            instructions=(
                "Use the MCP weather tool for current conditions. "
                "Give a short answer and mention the resolved location."
            ),
            model="gpt-5-nano",
            mcp_servers=[weather_server],
        )

        # Runner manages model calls, MCP tool execution, and observations.
        result = await Runner.run(agent, f"What is the current weather in {city}?")
        print("FINAL ANSWER:", result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
