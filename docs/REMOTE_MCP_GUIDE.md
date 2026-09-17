# Connecting Remote MCP Servers to Claude Desktop & Cursor

A complete architectural guide on configuring remote Model Context Protocol (MCP) endpoints using Server-Sent Events (SSE) or Streamable HTTP.

---

## The Common Problem

When connecting remote MCP servers (like MemorySync or custom cloud agents) to **Claude Desktop**, developers often add "url": "https://..." directly into claude_desktop_config.json. 

Claude Desktop ignores or fails on this configuration because its configuration engine **only executes local stdio processes (command + rgs)**, not direct network streams.

---

## 1. Claude Desktop Solution (claude_desktop_config.json)

To bridge remote SSE or HTTP endpoints to Claude Desktop's stdio transport, use the mcp-remote proxy bridge.

### Configuration File Locations:
* **macOS:** ~/Library/Application Support/Claude/claude_desktop_config.json
* **Windows:** %APPDATA%\Claude\claude_desktop_config.json

### Example Configuration:

`json
{
  "mcpServers": {
    "memorysync": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.memorysync.io/sse"
      ]
    },
    "custom-remote-tool": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://api.example.com/mcp",
        "--header",
        "Authorization: Bearer YOUR_API_TOKEN"
      ]
    }
  }
}
`

*Note: You must fully restart Claude Desktop after modifying this file.*

---

## 2. Cursor Configuration (.cursor/mcp.json or ~/.cursor/mcp.json)

Cursor natively supports remote URLs in its MCP configuration:

`json
{
  "mcpServers": {
    "memorysync": {
      "url": "https://mcp.memorysync.io/mcp"
    },
    "custom-authenticated-server": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_TOKEN"
      }
    }
  }
}
`

### Known Workaround in Cursor:
If Cursor's transport auto-detection fails on certain SSE endpoints (e.g., throwing transport negotiation errors), you can use the exact same mcp-remote stdio block from Claude Desktop above inside your .cursor/mcp.json.
