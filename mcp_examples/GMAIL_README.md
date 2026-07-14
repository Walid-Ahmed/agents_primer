# Gmail MCP agent: draft, review, then send

This example lets an OpenAI model read and search Gmail through MCP, create a real
draft, and optionally send it. Sending pauses until you type `SEND`.

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

- `gmail_server.py` publishes `search_emails`, `read_thread`, `create_draft`, and
  `send_draft` through MCP.
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

The example requests two scopes: `gmail.readonly` to search/read email and
`gmail.compose` to create/send drafts. It does not request the broad
`https://mail.google.com/` scope.

If you already ran the earlier draft-only version, delete `token.json` once and
run again so Google can ask you to approve the new read-only scope.

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

Read-only examples:

```bash
python mcp_examples/gmail_agent.py "Summarize my 3 newest emails"

python mcp_examples/gmail_agent.py \
  "Find the latest email from Alex and draft a short reply, but do not send it"
```

On the first run, a browser opens for Google authorization. The model creates the
draft and requests the send tool. Read the displayed recipient, subject, and body.
Type `SEND` to send; any other input cancels and leaves the draft in Gmail.

## Safety and concepts

- Test with your own address first and keep the approval check.
- Email content can contain prompt injection. The system prompt tells the model
  to treat email as data, but you must still review every external action.
- Delete `token.json` and revoke the app in your Google Account when finished.
- This is an agent: the model chooses tools and the application executes them in
  a loop. MCP is the standardized connection layer between the app and Gmail tools.
