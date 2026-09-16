# MemorySync Cursor Starter Template

> **Stop Cursor from forgetting your project architecture across chat restarts.**

This repository is a production-ready starter template configured with **MemorySync** and the **Model Context Protocol (MCP)**. It gives Cursor persistent, scoped memory across conversations, so you never have to re-explain your framework choices, database patterns, or pinned library versions.

---

## What's Included

* `.cursor/mcp.json`: Preconfigured with MemorySync remote MCP endpoints (both memory and live zero-signup docs).
* `.cursorrules`: Strict developer instructions instructing Cursor when to save decisions and how to recall them with zero context bloat.
* `examples/quickstart.py`: Minimal Python example demonstrating how to save and recall scoped facts programmatically.

---

## 60-Second Setup

### 1. Clone this template
```bash
git clone https://github.com/memorysyncio/memorysync-cursor-starter.git my-agent-project
cd my-agent-project
```

### 2. Open in Cursor
Open this folder in Cursor IDE:
```bash
cursor .
```

### 3. Verify MCP Connection
1. Open Cursor **Settings** (`Cmd + ,` or `Ctrl + ,`) > **Features** > **MCP**.
2. You will see two active servers:
   * `memorysync` (`https://mcp.memorysync.io/mcp`) — For persistent memory storage & semantic search.
   * `memorysync-docs` (`https://docs.memorysync.io/mcp`) — Instant live documentation search without sign-up.

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

* **Live MCP Docs Endpoint (Zero Signup):** [https://docs.memorysync.io/mcp](https://docs.memorysync.io/mcp)
* **Official Cursor Guide:** [docs.memorysync.io/guides/cursor](https://docs.memorysync.io/guides/cursor)
* **MemorySync Platform:** [memorysync.io](https://memorysync.io)
* **Console:** [app.memorysync.io](https://app.memorysync.io)

---

## License

MIT License. Free to use for personal and commercial projects.
