# Agents Primer

Minimal examples showing how an LLM receives a tool definition, decides whether
to use it, and returns a structured tool call for your application to execute.

## Concept guides

- [ReAct, Chain-of-Thought, and Reasoning Tokens](docs/agent_reasoning_concepts.md)
- [How an Agent Uses an External API](docs/agents_using_apis.md)
- [A Local Weather Agent with MCP](docs/direct_tools_vs_mcp.md)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add the API key for the provider you want to test to `.env`.

## Recommended learning order

Follow this path if you are learning agents and tool calling from scratch:

1. [`docs/agent_reasoning_concepts.md`](docs/agent_reasoning_concepts.md) — distinguish tool-using
   agents, ReAct, chain-of-thought prompting, and private reasoning tokens.
2. [`anthropic/one_round_tool_use.py`](anthropic/one_round_tool_use.py) — learn one complete Claude
   tool-use round: register a tool, inspect `tool_use`, execute Python, return a
   `tool_result`, and receive the final answer.
3. [`openai/one_round_tool_use.py`](openai/one_round_tool_use.py) — repeat the same one-round pattern
   with OpenAI and compare `function_call` with Anthropic's message format.
4. [`openai/multi_round_tool_loop.py`](openai/multi_round_tool_loop.py) — progress from one round to a
   bounded loop that handles dependent tool calls across multiple rounds.
5. [`docs/agents_using_apis.md`](docs/agents_using_apis.md) — understand the two
   API layers: your application calls the model API, while a selected tool may
   call a separate external API.
6. [`openai/live_weather_api_agent.py`](openai/live_weather_api_agent.py) — apply that design to
   live weather data from Open-Meteo.
7. [`docs/direct_tools_vs_mcp.md`](docs/direct_tools_vs_mcp.md) — learn why MCP moves
   tool discovery and execution behind a standard protocol.
8. [`mcp_examples/local_weather/weather_server.py`](mcp_examples/local_weather/weather_server.py) followed by
   [`mcp_examples/local_weather/weather_agent.py`](mcp_examples/local_weather/weather_agent.py) — inspect the
   local MCP tool first, then run the agent that launches and uses it.
9. [`mcp_examples/external_deepwiki_agent.py`](mcp_examples/external_deepwiki_agent.py)
   — connect to a hosted third-party MCP server for public information.
10. Optional real-action examples:
    [`mcp_examples/GMAIL_README.md`](mcp_examples/GMAIL_README.md) and
    [`mcp_examples/X_README.md`](mcp_examples/X_README.md). These introduce OAuth,
    private data, and explicit human approval before sending or publishing.

Suggested progression: **one tool round → provider comparison → multi-round agent
loop → external API → local MCP → hosted MCP → human-approved real actions**.

The first nine steps build on one another. Treat the Gmail and X examples as
optional advanced exercises because they require external credentials and can
affect real accounts.

## Anthropic example

```bash
python anthropic/one_round_tool_use.py
```

Look for a structured content block whose `type` is `tool_use`. The application
executes the function and returns a `tool_result` block to Claude.

## OpenAI example

```bash
python openai/one_round_tool_use.py
```

Look for a structured output item whose `type` is `function_call`. The application
executes the function and returns a `function_call_output` item to the model.

This first example intentionally demonstrates **one tool-call round**. It handles
multiple calls returned together, but it does not continue if the model asks for
another tool after seeing their results.

## OpenAI multi-round tool loop

```bash
python openai/multi_round_tool_loop.py
```

This example must first look up Alice's city and then use that result to request
the city's weather. Its bounded loop continues through dependent tool rounds until
the model returns a final answer.

## OpenAI agent using an external API

```bash
python openai/live_weather_api_agent.py "Toronto"
```

This example shows both API layers: the application calls OpenAI's model API,
while the model-selected tool calls Open-Meteo's live weather API. Open-Meteo
does not require a second API key for this small example.

## Local MCP weather agent

See the [MCP examples README](mcp_examples/README.md) for complete setup,
expected output, and troubleshooting.

```bash
python mcp_examples/local_weather/weather_agent.py "Toronto"
```

This version publishes the live Open-Meteo capability from a local MCP server.
The OpenAI agent launches the server over stdio, discovers its
`get_current_weather` tool, calls it, and receives the result through MCP. No
public MCP server or additional API key is required.

## External MCP server

```bash
python mcp_examples/external_deepwiki_agent.py
```

This example connects OpenAI's hosted MCP tool to DeepWiki's public MCP server and
asks a question about a public GitHub repository. It allow-lists only the read-only
`ask_question` tool. Send only public information to third-party MCP servers.

## What to notice

- Passing `tools` registers a tool; it does not execute the Python function.
- With the default `tool_choice="auto"`, the model decides whether a prompt needs it.
- Always inspect structured tool-call objects instead of guessing from model prose.
- Your application is responsible for executing local functions and returning results.
- Model decisions are probabilistic, so ambiguous prompts may vary across runs.
- Use `tool_choice` when your application must require, force, or forbid tools.

Weather values are intentionally hard-coded. This keeps the lesson focused on the
tool-calling protocol instead of requiring a second API.

## Project structure

```text
agents_primer/
├── anthropic/
│   ├── one_round_tool_use.py    # One Claude tool-use round
│   └── logging_utils.py         # Readable execution-log helpers
├── openai/
│   ├── one_round_tool_use.py    # One OpenAI tool-call round
│   ├── logging_utils.py         # Readable OpenAI execution logs
│   ├── multi_round_tool_loop.py # Multi-round dependent tool calls
│   └── live_weather_api_agent.py # Tool calling the live Open-Meteo API
├── docs/
│   ├── agent_reasoning_concepts.md # Agent and reasoning concepts
│   ├── agents_using_apis.md       # Model API versus tool API
│   └── direct_tools_vs_mcp.md     # Direct tools versus MCP
└── mcp_examples/
    ├── local_weather/          # Complete local MCP weather example
    │   ├── README.md
    │   ├── weather_server.py  # Publishes the MCP weather tool
    │   └── weather_agent.py   # Launches and uses the server
    ├── external_deepwiki_agent.py # Agent using a hosted MCP server
    ├── gmail_server.py / gmail_agent.py # Human-approved Gmail actions
    └── x_server.py / x_agent.py         # Human-approved X posting
```
