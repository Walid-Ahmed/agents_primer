"""Minimal agent using an external MCP server hosted by DeepWiki.

Run from the repository root:
    python mcp_examples/external_deepwiki_agent.py

Unlike weather_agent.py, this program does not launch a local MCP process.
OpenAI's Responses API connects to https://mcp.deepwiki.com/mcp, discovers the
allowed tool, calls it, and includes the result in the model's final answer.

Only send public information to this example. An external MCP server is a third
party and receives the arguments sent to its tool.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Add OPENAI_API_KEY to a .env file")

    client = OpenAI()
    response = client.responses.create(
        model="gpt-5-nano",
        tools=[
            {
                "type": "mcp",
                "server_label": "deepwiki",
                "server_description": "Answer questions about public GitHub repositories.",
                "server_url": "https://mcp.deepwiki.com/mcp",
                # Restrict the server to the one read-only tool this lesson needs.
                "allowed_tools": ["ask_question"],
                # Safe here only because the prompt contains public information and
                # ask_question is read-only. Sensitive/write tools should use approval.
                "require_approval": "never",
            }
        ],
        input=(
            "Use DeepWiki to explain the main purpose of the public repository "
            "openai/openai-agents-python in two sentences."
        ),
    )

    # Hosted MCP activity appears as structured items in response.output.
    for item in response.output:
        if item.type == "mcp_list_tools":
            print("MCP DISCOVERED:", [tool.name for tool in item.tools])
        elif item.type == "mcp_call":
            print(f"MCP CALL: {item.name}({item.arguments})")
            if item.error:
                print("MCP ERROR:", item.error)

    print("FINAL ANSWER:", response.output_text)


if __name__ == "__main__":
    main()
