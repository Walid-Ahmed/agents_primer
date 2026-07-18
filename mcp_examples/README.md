# MCP Examples

These examples show two ways an agent can use Model Context Protocol (MCP):

1. **Local MCP:** you own the server and run it as a local subprocess.
2. **External MCP:** OpenAI connects to a third-party server on the internet.
3. **Authenticated API through MCP:** a local MCP server safely wraps Gmail.
4. **Human-approved public action:** an agent drafts and publishes an X post.

## 1. Setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace the placeholder with your OpenAI API key:

```text
OPENAI_API_KEY=your_real_key_here
```

Run all commands below from the repository root, with the virtual environment
activated.

## 2. Local weather MCP example

Run:

```bash
python mcp_examples/weather_agent.py "Toronto"
```

Try another city:

```bash
python mcp_examples/weather_agent.py "Mexico City"
```

You do **not** start `weather_server.py` yourself. `weather_agent.py` launches it
automatically using the MCP stdio transport and closes it when the agent finishes.

### What happens

```text
weather_agent.py
    ↓ starts a local subprocess
weather_server.py
    ↓ publishes get_current_weather through MCP
OpenAI agent discovers and calls the tool
    ↓
weather_server.py calls Open-Meteo
    ↓
live weather returns to the agent
```

Expected output has this shape:

```text
MCP TOOLS: ['get_current_weather']
FINAL ANSWER: The current weather in Toronto, Canada is ...
```

This example requires:

- `OPENAI_API_KEY` for the model;
- internet access for OpenAI and Open-Meteo;
- no Open-Meteo API key;
- no public MCP deployment.

## 3. External DeepWiki MCP example

Run:

```bash
python mcp_examples/external_deepwiki_agent.py
```

### What happens

```text
external_deepwiki_agent.py
    ↓ calls OpenAI Responses API
OpenAI connects to https://mcp.deepwiki.com/mcp
    ↓ discovers the allow-listed ask_question tool
DeepWiki answers a question about a public GitHub repository
    ↓
OpenAI returns the final answer
```

Expected output has this shape:

```text
MCP DISCOVERED: ['ask_question']
MCP CALL: ask_question(...)
FINAL ANSWER: The repository provides ...
```

This example sends its tool arguments to an external third-party MCP server. Use
it only for public information. Do not put API keys, private repository content,
personal data, or other secrets in the prompt.

## 4. Files

| File | Role |
|---|---|
| `weather_server.py` | Local MCP server that publishes the weather tool |
| `weather_agent.py` | Agent that launches and uses the local server |
| `external_deepwiki_agent.py` | Agent using an internet-hosted MCP server |
| `gmail_server.py` | Local MCP wrapper for Gmail draft/send actions |
| `gmail_agent.py` | Agent with human approval required before sending |
| `x_server.py` | Local MCP wrapper for publishing through the X API |
| `x_agent.py` | Agent that previews a post and requires `POST` approval |

## 5. Gmail MCP example

See [`GMAIL_README.md`](GMAIL_README.md) for OAuth setup and exact commands. The
example creates a real Gmail draft but sends it only after you type `SEND`.

## 6. X posting MCP example

See [`X_README.md`](X_README.md) for X developer credentials and run commands.
The model drafts the content, but Python blocks the public action until you type
exactly `POST`.

## 7. Direct tools versus MCP

The repository's `openai/live_weather_api_agent.py` registers the weather function
directly with OpenAI. In the local MCP example, the server publishes the function
through a standard protocol and the agent discovers its schema at runtime.

```text
Direct tool: application owns schema + execution + tool loop
Local MCP:   MCP server owns schema + execution; agent connects over stdio
Hosted MCP:  external server owns schema + execution; OpenAI connects by URL
```

## 8. Troubleshooting

### `OPENAI_API_KEY` is missing

Confirm `.env` exists in the repository root and contains a real key:

```text
OPENAI_API_KEY=sk-...
```

### `No module named agents` or `No module named mcp`

Activate the virtual environment and reinstall dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### The local server disconnects

Run commands from the repository root. Do not add `print()` debugging statements
to `weather_server.py` stdout because stdio MCP uses stdout for protocol messages.

### A network request fails

Confirm the machine can reach:

- `api.openai.com`;
- `geocoding-api.open-meteo.com`;
- `api.open-meteo.com`;
- `mcp.deepwiki.com` for the external example.

The local weather example and external DeepWiki example both require internet
access, even though the weather MCP server itself runs locally.
