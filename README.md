# MemorySync Cursor Starter Template

> **Stop Cursor from forgetting your project architecture across chat restarts.**

This repository is a production-ready starter template configured with **MemorySync** and the **Model Context Protocol (MCP)**. It gives Cursor persistent, scoped memory across conversations, so you never have to re-explain your framework choices, database patterns, or pinned library versions.

---

## What's Included

* `.cursor/mcp.json`: Preconfigured with MemorySync remote MCP endpoints (both memory and live zero-signup docs).
* `.cursorrules`: Strict developer instructions instructing Cursor when to save decisions and how to recall them with zero context bloat.
* `setup.sh` & `setup.ps1`: Automated 1-click cross-platform setup scripts for macOS, Linux, and Windows.
* `tools/inspect_memory.sh` & `tools/inspect_memory.ps1`: Single-file, zero-dependency terminal memory inspector.
* `examples/minimal_mcp_client.py`: Minimal Python example demonstrating how to interact with MCP programmatically.

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
                               | 2. Sub-50ms Hybrid Recall
                               v
+-------------------------------------------------------------+
|      Fresh Chat Session: Automatically applies past rule    |
+-------------------------------------------------------------+
```

1. **Zero Context Bloat:** Injects ~45 tokens of exact recalled facts instead of 8,000+ tokens of raw chat history.
2. **Multi-Project Isolation:** Memories are strictly scoped by project so your backend rules never leak into your frontend.
3. **Inspectability:** Every recalled fact references a verifiable memory ID.

---

## Documentation & Resources

* **Cursor Guide:** [https://docs.memorysync.io/guides/cursor](https://docs.memorysync.io/guides/cursor)
* **MCP Integration Docs:** [https://docs.memorysync.io/mcp/overview](https://docs.memorysync.io/mcp/overview)
* **Live Zero-Signup Docs MCP:** [https://docs.memorysync.io/mcp](https://docs.memorysync.io/mcp)
