# Gmail MCP agent: draft, review, then send

This example lets an OpenAI model use Gmail through MCP. It creates a real Gmail
draft, then pauses before sending it. The email is sent only if you type `SEND`.

## Why this uses a local MCP server

Google provides an official remote Gmail MCP server at
`https://gmailmcp.googleapis.com/mcp/v1`, currently in Developer Preview. It
includes `create_draft`, but does **not** currently expose a send tool. Google
expects you to review the draft and send it from Gmail.

To teach both actions, this example uses a small local MCP server around Google's
official Gmail API:

```text
your prompt -> OpenAI model -> local MCP server -> Gmail API
                                      |
                               SEND approval gate
```

## Files

- `gmail_server.py` publishes `create_draft` and `send_draft` through MCP.
- `gmail_agent.py` gives those tools to the model and runs the tool loop.
- `credentials.json` is your OAuth client secret. Never commit it.
- `token.json` is created after login. Never commit it.

## One-time Google setup

1. Create or select a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Gmail API**.
3. Configure the OAuth consent screen. For personal testing, add your Google
   account as a test user if Google requests one.
4. Create an OAuth client ID with application type **Desktop app**.
5. Download it, rename it `credentials.json`, and put it in the repository root.

The example requests `gmail.compose`, which permits creating and sending drafts
without granting full mailbox access.

## Install and run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your OpenAI API key in `.env`, then test with your own recipient address:

```bash
python mcp_examples/gmail_agent.py \
  "Email me@example.com to say this is a Gmail MCP test"
```

On the first run, a browser opens for Google authorization. The model creates the
draft and requests the send tool. Read the displayed recipient, subject, and body.
Type `SEND` to send; any other input cancels and leaves the draft in Gmail.

## Safety and concepts

- Test with your own address first and keep the approval check.
- Email content can contain prompt injection. Never let untrusted email text
  authorize sending or other mailbox changes.
- Delete `token.json` and revoke the app in your Google Account when finished.
- This is an agent: the model chooses tools and the application executes them in
  a loop. MCP is the standardized connection layer between the app and Gmail tools.
