# How an Agent Uses an External API

An agent usually reaches an external API **through a tool**. The model decides
which capability it needs, while application code performs the real HTTP request.

## The two API layers

An API-using agent commonly talks to two different services:

| Layer | Called by | Purpose |
|---|---|---|
| Model API | Your application | Ask the model what to say or which tool to use |
| External API | Your tool function | Retrieve data or perform an action |

For the weather example in this repository:

```text
Python application ──request──> OpenAI Responses API
                         │
                         │ model requests get_current_weather
                         ▼
                  Python tool function
                         │
                         ├──request──> Open-Meteo Geocoding API
                         └──request──> Open-Meteo Forecast API
                         │
                         ▼
               tool result returned to model
                         │
                         ▼
                    final answer
```

## Why wrap an API in a tool?

The tool definition gives the model a small, structured interface. The model does
not need to know endpoint URLs, authentication headers, or response formats.

For example, the model sees a contract like:

```python
{
    "name": "get_current_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}
```

Your application owns the implementation:

```python
def get_current_weather(city: str) -> str:
    # Call an external service and return useful data.
    ...
```

This separation provides several benefits:

- the model receives a simple interface instead of API-specific details;
- secrets remain in application code and environment variables;
- code can validate arguments before sending requests;
- the application can enforce permissions, timeouts, retries, and budgets;
- the external API can be replaced without changing the model-facing schema.

## What the model does—and does not do

The model:

- reads the user request and available tool descriptions;
- decides whether a tool is needed;
- returns a structured tool name and arguments;
- uses the returned result to write its answer.

The application:

- validates the requested tool and its arguments;
- calls the external API;
- handles errors and timeouts;
- returns the result to the model.

Unless a provider offers a hosted tool, the model does **not** directly execute
your Python function or send the HTTP request.

## Is this ReAct?

A single tool call is the basic building block of ReAct:

```text
decide → act with a tool → observe its result → answer
```

If the application repeatedly lets the model choose another tool after each
observation, it becomes a multi-round ReAct-style agent loop. The weather example
uses one round because one tool can complete the task.

This example does not request visible Chain-of-Thought and does not configure or
inspect reasoning tokens. Those concepts affect reasoning, while the tool controls
access to external data.

## Production considerations

The example is intentionally small. For a production agent, also consider:

- never place API keys in prompts or tool results;
- validate model-generated arguments as untrusted input;
- use request timeouts and limited retries;
- return compact, relevant data instead of an entire API response;
- require confirmation before tools perform consequential actions;
- log tool name, duration, success, and errors without logging secrets;
- limit the number of tool rounds to prevent infinite loops;
- follow the external service's usage policy and attribution requirements.

## Run the example

Open-Meteo does not require an API key for this small non-commercial example. You
still need an OpenAI API key because the application uses the OpenAI model API.

```bash
python openai/api_tool_agent.py
```

The example asks about Toronto by default. Pass another city as an argument:

```bash
python openai/api_tool_agent.py "Mexico City"
```
