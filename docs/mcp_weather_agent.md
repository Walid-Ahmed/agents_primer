# A Local Weather Agent with MCP

This example publishes live weather as a local MCP tool and lets an OpenAI agent
discover and use it.

## Architecture

```text
User prompt
    ↓
OpenAI Agents SDK
    ↓ starts local process and lists tools over MCP stdio
weather_server.py
    ↓ publishes get_current_weather
Open-Meteo APIs
    ↓ live weather result
MCP server → agent → final answer
```

## Why two files?

MCP separates the capability provider from the AI application:

- `weather_server.py` owns the tool and calls Open-Meteo.
- `weather_agent.py` connects to the server and uses whatever tools it publishes.

The direct version in `openai/api_tool_agent.py` declares the schema, executes the
function, and returns the result itself. The MCP version moves that interface and
execution behind a standard protocol.

## What stdio means

The agent launches the MCP server as a local subprocess. They communicate using
JSON-RPC messages over standard input and output. Nothing is deployed publicly,
and no remote MCP server receives the prompt or weather request.

Because stdout carries MCP protocol messages, server debugging output must go to
stderr or a log file—not stdout.

## Run it

Install the dependencies and add `OPENAI_API_KEY` to `.env`, then run:

```bash
python mcp_examples/weather_agent.py "Toronto"
```

The program prints the tool discovered from the MCP server, followed by the
agent's final answer.

## What happens automatically

The OpenAI Agents SDK:

1. starts the MCP server;
2. calls MCP `tools/list` to discover `get_current_weather`;
3. gives that schema to the model;
4. sends the model's tool request to the MCP server;
5. returns the server's result to the model;
6. repeats if necessary and produces the final answer;
7. closes the MCP server process.

This is ReAct-style behavior because the runtime manages the cycle of deciding,
acting with a tool, observing the result, and continuing. It does not require
visible Chain-of-Thought or expose private model reasoning.

## Why the tool filter matters

The agent uses an allow-list containing only `get_current_weather`. Tool filtering
keeps the model's choices small and prevents newly added server tools from becoming
available to this agent accidentally.

## Production notes

This is a local teaching example. In a real application:

- validate tool arguments as untrusted input;
- handle network errors and retries;
- use approvals for sensitive or write-capable tools;
- log tool activity without secrets;
- keep MCP dependencies versioned;
- use Streamable HTTP when the MCP server must run as a separate service.

## Local versus external MCP

This guide's weather server is local and controlled by you. The repository also
includes `external_deepwiki_agent.py`, which connects to a third-party MCP server
over the internet. Use the external example only with public repository questions;
never send secrets or private content to an MCP server you do not control.
