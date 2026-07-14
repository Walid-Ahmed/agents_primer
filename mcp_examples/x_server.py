"""Local MCP server exposing one consequential action: publish an X post."""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from requests_oauthlib import OAuth1Session

load_dotenv()
mcp = FastMCP("x-tools")


@mcp.tool()
def post_to_x(text: str) -> dict:
    """Publish text to the authenticated X account. This is a public action."""
    text = text.strip()
    if not text:
        raise ValueError("Post text cannot be empty.")
    if len(text) > 280:
        raise ValueError("This primer limits posts to 280 characters.")

    names = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing X credentials: {', '.join(missing)}")

    x = OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    response = x.post("https://api.x.com/2/tweets", json={"text": text}, timeout=30)
    response.raise_for_status()
    data = response.json()["data"]
    return {"posted": True, "post_id": data["id"], "text": data["text"]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
