# What this file does: drafts an X post and publishes only after user approval.
"""Ask the user for an idea, draft an X post, and publish only after approval."""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

MODEL = "gpt-5-nano"


async def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY in .env first.")

    # The program asks the human for the topic when none is passed on the command line.
    idea = " ".join(sys.argv[1:]).strip() or input("What would you like to post about? ").strip()
    if not idea:
        raise SystemExit("No post idea was provided.")

    server = StdioServerParameters(command=sys.executable, args=["mcp_examples/x_server.py"])
    client = OpenAI()

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tool = (await session.list_tools()).tools[0]
            tools = [
                {
                    "type": "function",
                    "name": mcp_tool.name,
                    "description": mcp_tool.description or "",
                    "parameters": mcp_tool.inputSchema,
                }
            ]

            response = client.responses.create(
                model=MODEL,
                instructions=(
                    "Turn the user's idea into one clear, natural X post of at most 280 "
                    "characters. Preserve the user's meaning, do not invent facts, then "
                    "request the post_to_x tool. Never claim it was posted unless the "
                    "tool succeeds."
                ),
                input=idea,
                tools=tools,
            )

            while True:
                calls = [item for item in response.output if item.type == "function_call"]
                if not calls:
                    print("FINAL ANSWER:", response.output_text)
                    return

                outputs = []
                for call in calls:
                    arguments = json.loads(call.arguments)
                    draft = arguments["text"]
                    print("\nDRAFT POST:\n" + draft)
                    print(f"\nCHARACTERS: {len(draft)}/280")

                    # The approval check is application code. The model cannot bypass it.
                    approval = input("Type POST to publish, or anything else to cancel: ")
                    if approval != "POST":
                        result_text = "User cancelled. Nothing was posted."
                    else:
                        result = await session.call_tool(call.name, arguments)
                        result_text = "\n".join(
                            item.text for item in result.content if hasattr(item, "text")
                        )
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": result_text,
                        }
                    )

                response = client.responses.create(
                    model=MODEL,
                    previous_response_id=response.id,
                    input=outputs,
                    tools=tools,
                )


if __name__ == "__main__":
    asyncio.run(main())
