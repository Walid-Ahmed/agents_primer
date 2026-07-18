# Local Weather MCP Agent

This example shows how an OpenAI agent discovers and calls a tool published by a
local Model Context Protocol (MCP) server. The tool retrieves live weather from
[Open-Meteo](https://open-meteo.com/).

## Files

- [`weather_server.py`](weather_server.py) creates the local MCP server, publishes
  `get_current_weather`, and calls Open-Meteo.
- [`weather_agent.py`](weather_agent.py) starts the server, discovers its tool,
  gives that tool to the model, and prints the final answer.

Keep these files together: the agent locates the server beside itself using
`Path(__file__).with_name("weather_server.py")`.

## Architecture

```text
User question
    ↓
weather_agent.py
    ↓ starts a local subprocess over stdio
weather_server.py
    ↓ publishes get_current_weather through MCP
Open-Meteo APIs
    ↓ return live weather
MCP server → agent → model → final answer
```

The model does not run `weather_server.py` or call Open-Meteo directly. It asks
for the discovered MCP tool, and the agent runtime routes that request to the
local server.

## Setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```text
OPENAI_API_KEY=your_real_key_here
```

## Run

Run the agent from the repository root:

```bash
python mcp_examples/local_weather/weather_agent.py "Toronto"
```

Try another city:

```bash
python mcp_examples/local_weather/weather_agent.py "Mexico City"
```

Do not start `weather_server.py` separately. The agent launches it automatically
and closes it when execution finishes.

Expected output has this shape:

```text
MCP TOOLS: ['get_current_weather']
FINAL ANSWER: The current weather in Toronto, Canada is ...
```

## Execution flow

1. `weather_agent.py` starts `weather_server.py` as a local Python subprocess.
2. They communicate through MCP over standard input and output (`stdio`).
3. The agent asks the server for its available tools.
4. The server returns the schema for `get_current_weather`.
5. The model chooses that tool for the weather question.
6. The server geocodes the city and requests current conditions from Open-Meteo.
7. The tool result returns to the model, which writes the final answer.
8. The context manager closes the local server process.

## Important stdio rule

Do not add ordinary `print()` calls to `weather_server.py`. MCP uses the server's
stdout for protocol messages, so debugging text there can corrupt the connection.
Log server diagnostics to stderr or a file instead. Printing from
`weather_agent.py` is safe because it is the client process.

## Requirements

- `OPENAI_API_KEY` for the model
- Internet access for OpenAI and Open-Meteo
- No Open-Meteo API key
- No public MCP deployment

## Related examples

- [`../../openai/live_weather_api_agent.py`](../../openai/live_weather_api_agent.py)
  exposes the weather function directly without MCP.
- [`../external_deepwiki_agent.py`](../external_deepwiki_agent.py) connects to a
  hosted third-party MCP server instead of launching a local one.
- [`../../docs/direct_tools_vs_mcp.md`](../../docs/direct_tools_vs_mcp.md) explains
  the architectural differences in more detail.
