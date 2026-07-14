# ReAct, Chain-of-Thought, and Reasoning Tokens

This guide separates three ideas that are often mixed together:

1. **Chain-of-Thought (CoT)** helps a model reason through a problem.
2. **Reasoning tokens** give some models internal compute for harder problems.
3. **ReAct** connects reasoning to actions through an application-controlled loop.

The simplest distinction is:

> CoT and reasoning tokens affect how a model reaches an answer. ReAct lets a
> system interact with tools and the outside world while solving a task.

## Quick comparison

| Concept | What it is | Where it lives | Can it act? | Main controller |
|---|---|---|---|---|
| Chain-of-Thought | A reasoning/prompting pattern | Prompt and model output | No | Developer and model |
| Reasoning tokens | Model-native internal reasoning | Model/API | No | Model and API settings |
| ReAct | A reason-act-observe pattern | Prompt plus runtime loop | Yes, when tools are connected | Model and application |
| Agent framework | Code that manages tools and the loop | Application | Yes | Developer |

## 1. Chain-of-Thought (CoT)

Chain-of-Thought means using intermediate reasoning to help solve a multi-step
problem. A classic prompt might say:

```text
Solve the problem step by step, then give a concise final answer.
```

CoT can help with tasks such as:

- multi-step arithmetic;
- logic and constraint problems;
- planning;
- explaining how a conclusion follows from evidence.

CoT alone is **not agentic**. It cannot search the web, read a database, send an
email, or execute code. It only changes the model's reasoning and response.

### A useful mental model

Language models generate tokens one at a time. Earlier generated tokens become
context for later tokens. Intermediate reasoning can therefore make a correct
final answer more likely by giving later predictions more relevant context.

### Practical caution

Do not design an application that depends on receiving a model's private internal
reasoning. Ask for a short explanation, evidence, calculations, or a verification
summary when those are useful to the user.

## 2. Reasoning tokens

Some models can spend additional tokens or compute reasoning internally before
returning an answer. APIs may call these **reasoning tokens**, **thinking tokens**,
or **extended thinking**, depending on the provider.

Reasoning tokens differ from classic visible CoT:

| Visible CoT | Model-native reasoning |
|---|---|
| Requested mainly through prompting | Supported by a reasoning-capable model/API |
| Intermediate explanation may appear in the answer | Internal reasoning may be hidden or summarized |
| Adds visible output tokens | May consume billed tokens without exposing them verbatim |
| Developer shapes the requested explanation | Model and API settings control reasoning effort |

Reasoning tokens can improve difficult answers, but they still do not give the
model access to external systems. A model can reason deeply and still lack today's
weather, private files, or permission to take an action.

## 3. ReAct: Reason + Act

ReAct is a pattern that alternates between deciding what is needed and interacting
with tools:

```text
User request
    ↓
Model decides the next step
    ↓
Tool call ──→ Application executes tool
    ↑                    ↓
    └──── Tool result / observation
    ↓
Model answers or chooses another tool
```

The loop is commonly summarized as:

```text
Reason → Act → Observe → Repeat → Final answer
```

The model does not normally execute a local function by itself. Instead:

1. The application sends the prompt and tool definitions to the model.
2. The model returns a structured tool request.
3. The application validates and executes that request.
4. The application sends the tool result back to the model.
5. The model answers or requests another tool.

This execution loop is what turns tool-calling into an agentic system.

## Registering a tool is not executing it

Suppose an application defines this function:

```python
def get_weather(city: str) -> str:
    return weather_service.lookup(city)
```

The model usually receives only a description and input schema:

```python
weather_tool = {
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}
```

The schema tells the model **what it may request**. Application code decides
whether the request is safe, runs the function, and returns the result.

## A minimal ReAct-style loop

The exact API objects differ between providers, but the control flow is similar:

```python
messages = [{"role": "user", "content": user_prompt}]

while True:
    response = call_model(messages=messages, tools=tool_schemas)

    if not response.has_tool_calls():
        print(response.final_text())
        break

    messages.append(response.as_assistant_message())

    for call in response.tool_calls():
        # Production systems should validate arguments and permissions here.
        result = execute_tool(call.name, call.arguments)
        messages.append(make_tool_result(call.id, result))
```

This loop is conceptually ReAct even when the model does not reveal a literal
`Thought:` string. Modern APIs normally use structured tool calls instead of
parsing `Action:` text from free-form model output.

## Prompt-only ReAct versus a working agent

A prompt can ask a model to write:

```text
Thought: I need the current weather.
Action: get_weather("Toronto")
Observation: ...
```

Without an executor, this is only formatted text. The model may describe an action,
but no action occurs.

A working agent also needs:

- registered tool schemas;
- code that detects structured tool requests;
- tool implementations;
- argument validation and authorization;
- a loop that returns observations to the model;
- stopping conditions and error handling.

## How frameworks fit

Frameworks such as LangChain and LangGraph can manage the tool loop, conversation
state, retries, routing, and stopping conditions.

- **CoT:** mostly a model/prompt concern; a framework can pass the prompt through.
- **Reasoning tokens:** mostly a model/API concern; a framework passes configuration
  and response metadata through.
- **ReAct:** an orchestration concern; the framework can execute tools and feed
  results back to the model.

You do not need a framework for a small agent. A plain `while` loop is often the
best way to learn the protocol. Frameworks become useful when the workflow needs
persistence, branching, approvals, recovery, or several cooperating components.

## ReAct versus plan-and-execute

ReAct chooses the next step from the latest observation. This makes it adaptive,
but it can lose sight of long-term goals.

Plan-and-execute creates a broader plan first, then performs its steps. An executor
may itself use a ReAct loop.

| Dimension | ReAct | Plan-and-execute |
|---|---|---|
| Planning style | One step at a time | Upfront roadmap |
| Best for | Dynamic and uncertain tasks | Structured, long-horizon tasks |
| Adaptability | High | Requires replanning when conditions change |
| Complexity | Lower | Higher |
| Common failure | Loops or wasted calls | Brittle or outdated plan |

Hybrid agents often plan at a high level and use ReAct-style execution within each
step.

## Common misconceptions

### "A tool in the prompt means the model used it"

No. Check the API response for a structured tool-call object. Never infer tool use
from prose.

### "The model runs my Python function"

Usually no. The model requests the function; your application executes it.

### "ReAct requires exposing private reasoning"

No. The system needs decisions, tool calls, observations, and final answers—not a
verbatim private scratchpad.

### "CoT creates an agent"

No. CoT can improve reasoning inside an agent, but actions require tools and an
execution loop.

### "A framework makes tool calls safe"

Not automatically. Your application must still enforce permissions, validation,
timeouts, budgets, and approval rules.

## Choosing the right pattern

Use direct answering when the model already has enough information.

Use stronger reasoning when the task is difficult but self-contained.

Use tools when the task needs:

- current or private information;
- exact calculation or code execution;
- file or database access;
- side effects such as sending or updating something.

Use ReAct when the model must choose tools iteratively based on earlier results.

Use plan-and-execute when a long task benefits from an explicit roadmap and progress
tracking.

## Production checklist

Before allowing an agent to execute real tools, add:

- clear, non-overlapping tool descriptions;
- strict argument schemas and validation;
- authorization checks outside the model;
- confirmation before destructive or external actions;
- time, cost, and iteration limits;
- retries and useful error results;
- logs for tool requests, results, and final outcomes;
- evaluations using prompts that should and should not trigger each tool.

## Final takeaway

```text
CoT                 → improves visible step-by-step reasoning
Reasoning tokens    → provide model-native internal reasoning
Tool calling        → lets the model request an external capability
ReAct               → repeats decision, tool call, and observation
Agent framework     → implements and manages that loop in application code
```

Reasoning makes an answer smarter. Tools make external information and actions
available. The execution loop connects the two into an agent.
