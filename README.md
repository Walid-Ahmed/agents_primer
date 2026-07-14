# Agents Primer

Minimal examples showing how an LLM receives a tool definition, decides whether
to use it, and returns a structured tool call for your application to execute.

## Concept guides

- [ReAct, Chain-of-Thought, and Reasoning Tokens](docs/react_and_cot.md)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add the API key for the provider you want to test to `.env`.

## Anthropic example

```bash
python anthropic/tool_use.py
```

Look for a structured content block whose `type` is `tool_use`. The application
executes the function and returns a `tool_result` block to Claude.

## OpenAI example

```bash
python openai/tool_use.py
```

Look for a structured output item whose `type` is `function_call`. The application
executes the function and returns a `function_call_output` item to the model.

## What to notice

- Passing `tools` registers a tool; it does not execute the Python function.
- With the default `tool_choice="auto"`, the model decides whether a prompt needs it.
- Always inspect structured tool-call objects instead of guessing from model prose.
- Your application is responsible for executing local functions and returning results.
- Model decisions are probabilistic, so ambiguous prompts may vary across runs.
- Use `tool_choice` when your application must require, force, or forbid tools.

Weather values are intentionally hard-coded. This keeps the lesson focused on the
tool-calling protocol instead of requiring a second API.
