# MemorySync Cursor Starter Template

> **Stop Cursor from forgetting your project architecture across chat restarts.**

This repository is a production-ready starter template configured with **MemorySync** and the **Model Context Protocol (MCP)**. It gives Cursor persistent, scoped memory across conversations, so you never have to re-explain your framework choices, database patterns, or pinned library versions.

---

## What's Included

* `server.py`: Runnable, zero-dependency standard MCP stdio server implementing the full Model Context Protocol (MCP 2024-11-05) for Cursor, Claude Desktop, and AI agents.
* `Dockerfile` & `docker-compose.yml`: Containerized deployment running the MCP server over stdio.
* `.cursor/mcp.json`: Preconfigured with MemorySync remote MCP endpoints (both memory and live zero-signup docs).
* `.cursorrules`: Strict developer instructions instructing Cursor when to save decisions and how to recall them with zero context bloat.
* `setup.sh` & `setup.ps1`: Automated 1-click cross-platform setup scripts for macOS, Linux, and Windows.
* `tools/inspect_memory.sh` & `tools/inspect_memory.ps1`: Single-file, zero-dependency terminal memory inspector.
* `examples/minimal_mcp_client.py`: Minimal Python example demonstrating how to interact with MCP programmatically.

---

## Get an API key (no account needed)

`memorysync_read_docs` and the `memorysync-docs` server work without a key. The memory tools need one. You can get an evaluation key without signing up:

- **In the browser:** open [memorysync.io/try](https://memorysync.io/try) and press **Create my key**.
- **From a terminal:**
  ```bash
  curl --request POST https://api.memorysync.io/evaluation/keys \
    --header "Content-Type: application/json" \
    --data '{"agent_caller":"cursor"}'
  ```
  The response includes `api_key`, `default_user_id`, when the key expires (`expires_at`) and how many writes and searches it allows (`limits`).

Then set both values where `server.py` reads them (the memory inspector reads the key too):

```bash
# macOS / Linux
export MEMORYSYNC_API_KEY="<api_key>"
export MEMORYSYNC_USER_ID="<default_user_id>"
```

```powershell
# Windows PowerShell
$env:MEMORYSYNC_API_KEY = "<api_key>"
$env:MEMORYSYNC_USER_ID = "<default_user_id>"
```

`server.py` sends the key as `X-API-Key` and the user id as `X-End-User-ID`. Every memory is saved and searched under that end user, so give each person their own id. Without `MEMORYSYNC_USER_ID`, everyone shares `default-user`.

An evaluation key stops working at `expires_at`. To keep a browser key, add your email on [memorysync.io/try](https://memorysync.io/try). For a permanent key, [create a free account](https://app.memorysync.io/register).

---

## Running the MCP Server (stdio)

Run the server directly with Python 3:
```bash
python3 server.py
```

Or connect it to Claude Desktop / Cursor using stdio configuration:
```json
{
  "mcpServers": {
    "memorysync": {
      "command": "python3",
      "args": ["/path/to/memorysync-cursor-starter/server.py"],
      "env": {
        "MEMORYSYNC_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Supported MCP Tools:
* `memorysync_search`: Semantic search over persistent long-term memories, ranked by meaning.
* `memorysync_add`: Save a new durable memory, preference, or architectural decision.
* `memorysync_read_docs`: Query official MemorySync API, SDK, and integration documentation on demand. Needs no key.
* `memorysync_get`: Read one memory in full, by the id a search returned.
* `memorysync_related`: Find memories connected to a topic.
* `memorysync_decisions`: List recorded decisions and the facts that contradict each other.
* `memorysync_forget`: Delete memories. Shows what would be deleted first, and deletes nothing until you confirm.

---

## 60-Second Setup

### 1. Clone this template
```bash
git clone https://github.com/memorysyncio/memorysync-cursor-starter.git my-agent-project
cd my-agent-project
```

### 2. Run Automated Setup

**Option A: Local Terminal (macOS / Linux / Windows)**
- **macOS / Linux:**
  ```bash
  chmod +x setup.sh && ./setup.sh
  ```
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\setup.ps1
  ```

**Option B: Docker (Containerized Testing)**
```bash
# Verify connection inside container
docker compose run --rm memorysync-starter

# Run programmatic Python client test
docker compose run --rm test
```

### 3. Open in Cursor
Open this folder in Cursor IDE:
```bash
cursor .
```

### 4. Verify MCP Connection
1. Open Cursor **Settings** (`Cmd + ,` or `Ctrl + ,`) > **Features** > **MCP**.
2. You will see two active servers:
   * `memorysync` (`https://mcp.memorysync.io/mcp`) — For persistent memory storage & semantic search.
   * `memorysync-docs` (`https://docs.memorysync.io/mcp`) — Instant live documentation search without sign-up.

---

## Terminal Memory Inspector

Inspect and verify saved memories directly from your terminal without opening a browser:

```bash
# macOS / Linux
./tools/inspect_memory.sh ping
./tools/inspect_memory.sh stats -k "ms_live_..."
./tools/inspect_memory.sh query "PostgreSQL configuration" -k "ms_live_..."

# Windows PowerShell
.\tools\inspect_memory.ps1 -Command ping
.\tools\inspect_memory.ps1 -Command stats -ApiKey "ms_live_..."
.\tools\inspect_memory.ps1 -Command query -Query "PostgreSQL configuration" -ApiKey "ms_live_..."
```

---

## How It Works

```text
+-------------------------------------------------------------+
|                       Cursor Composer                       |
+------------------------------+------------------------------+
                               | 1. Store Decision (e.g. "We use FastAPI async")
                               v
+-------------------------------------------------------------+
|                  MemorySync Remote MCP Server               |
|                  (https://mcp.memorysync.io)                |
+------------------------------+------------------------------+
                               | 2. Hybrid keyword + vector recall
                               v
+-------------------------------------------------------------+
|      Fresh Chat Session: Automatically applies past rule    |
+-------------------------------------------------------------+
```

1. **Small context:** Injects the few facts relevant to the task instead of replaying raw chat history.
2. **Multi-Project Isolation:** Memories are strictly scoped by project so your backend rules never leak into your frontend.
3. **Inspectability:** Every recalled fact references a verifiable memory ID.

---

## Documentation & Resources

* **Cursor Guide:** [https://docs.memorysync.io/guides/cursor](https://docs.memorysync.io/guides/cursor)
* **MCP Integration Docs:** [https://docs.memorysync.io/mcp/overview](https://docs.memorysync.io/mcp/overview)
* **Live Zero-Signup Docs MCP:** [https://docs.memorysync.io/mcp](https://docs.memorysync.io/mcp)
