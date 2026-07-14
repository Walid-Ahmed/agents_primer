# X MCP agent: write, review, then post

This example asks what you want to say, lets an OpenAI model draft one short X
post, and publishes it through a local MCP server only after you type `POST`.

```text
your idea -> OpenAI model -> proposed post_to_x call
                                  |
                           human types POST
                                  |
                     local MCP server -> X API
```

## Files

- `x_agent.py`: host, OpenAI tool loop, preview, and approval gate
- `x_server.py`: MCP server that publishes the `post_to_x` tool

## X developer setup

1. Create an X developer account, project, and app in the
   [X Developer Portal](https://developer.x.com/).
2. Give the app **Read and write** permission.
3. Generate the API key/secret and user access token/secret for your account.
4. Add the four values to `.env`—never commit them.

```text
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

The API uses user-context authentication to post on behalf of an account. This
minimal example uses OAuth 1.0a; an app-only bearer token cannot publish a post.
X API access and usage charges depend on your current developer plan.

## Install and run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ask interactively:

```bash
python mcp_examples/x_agent.py
```

Or provide the idea directly:

```bash
python mcp_examples/x_agent.py \
  "Share that I learned how MCP connects an agent to external APIs"
```

The model drafts the post and requests `post_to_x`. Review the displayed text and
character count. Type exactly `POST` to publish; any other input cancels.

## Why approval is outside the prompt

Publishing is a public external action. A system prompt such as “ask first” is
useful guidance but is not a hard security boundary. Here, Python intercepts the
tool call before the MCP server receives it, so the action cannot run without the
literal confirmation token.

## Safety

- Test with a non-sensitive message and verify which account owns the token.
- Never paste API credentials into the user prompt.
- Review names, claims, links, and private information before posting.
- Revoke or rotate credentials in the X developer portal if exposed.

Official references:

- [Create a Post](https://docs.x.com/x-api/posts/create-post)
- [Manage Posts quickstart](https://docs.x.com/x-api/posts/manage-tweets/quickstart)
- [OAuth 1.0a user context](https://docs.x.com/fundamentals/authentication/oauth-1-0a/overview)
