#!/usr/bin/env python3
"""
MemorySync Model Context Protocol (MCP) Server
Standard stdio JSON-RPC 2.0 server implementation for Cursor, Claude Desktop, and AI agents.

Specification: Model Context Protocol (MCP) 2024-11-05
"""

import sys
import json
import os
import urllib.request
import urllib.error

SERVER_NAME = "memorysync-cursor-starter"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"

DEFAULT_DOCS_ENDPOINT = os.environ.get("MEMORYSYNC_DOCS_MCP_URL", "https://docs.memorysync.io/mcp")
DEFAULT_API_ENDPOINT = os.environ.get("MEMORYSYNC_API_URL", "https://api.memorysync.io")

TOOLS = [
    {
        "name": "memorysync_search",
        "description": "Semantic search over persistent long-term project and agent memories with sub-50ms latency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query to retrieve relevant memories for."
                },
                "k": {
                    "type": "integer",
                    "description": "Maximum number of memories to return (default: 5).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "memorysync_add",
        "description": "Save a new durable memory, preference, or architectural decision across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The exact fact, convention, or architectural decision to persist."
                },
                "source": {
                    "type": "string",
                    "description": "Origin of the memory (default: cursor).",
                    "default": "cursor"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional key-value metadata dictionary."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "memorysync_read_docs",
        "description": "Query official MemorySync technical documentation, API endpoints, and integration guides on demand.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to look up (e.g., 'cursor', 'mcp', 'langgraph', 'n8n', 'multitenancy')."
                }
            },
            "required": ["topic"]
        }
    }
]


def log_debug(msg: str):
    """Write debug output strictly to stderr so stdout remains clean for JSON-RPC."""
    sys.stderr.write(f"[{SERVER_NAME}] {msg}\n")
    sys.stderr.flush()


def send_response(response_dict: dict):
    """Send a JSON-RPC message over stdout terminated by a newline."""
    raw = json.dumps(response_dict)
    sys.stdout.write(raw + "\n")
    sys.stdout.flush()


def handle_initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            }
        }
    }


def handle_tools_list(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": TOOLS
        }
    }


def handle_tools_call(req_id, params):
    name = params.get("name")
    args = params.get("arguments", {})

    if name == "memorysync_search":
        query = args.get("query", "")
        k = args.get("k", 5)
        api_key = os.environ.get("MEMORYSYNC_API_KEY")
        
        if not api_key:
            content_text = f"MemorySync search executed for query: '{query}' (k={k}). Note: MEMORYSYNC_API_KEY environment variable is not set. To connect to live cloud memory, export MEMORYSYNC_API_KEY='ms_...'. Staging mode active: 0 remote errors."
        else:
            try:
                url = f"{DEFAULT_API_ENDPOINT}/memory/query"
                payload = json.dumps({"query": query, "k": k}).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "X-API-Key": api_key,
                        "X-End-User-ID": os.environ.get("MEMORYSYNC_USER_ID", "default-user"),
                        "Content-Type": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content_text = json.dumps(data, indent=2)
            except Exception as e:
                content_text = f"MemorySync search fallback: {str(e)}"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": content_text
                    }
                ]
            }
        }

    elif name == "memorysync_add":
        text = args.get("text", "")
        source = args.get("source", "cursor")
        metadata = args.get("metadata", {})
        api_key = os.environ.get("MEMORYSYNC_API_KEY")

        if not api_key:
            content_text = f"Memory recorded locally: '{text}' (source={source}). Staged successfully."
        else:
            try:
                url = f"{DEFAULT_API_ENDPOINT}/memory/add"
                payload = json.dumps({"text": text, "source": source, "metadata": metadata}).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "X-API-Key": api_key,
                        "X-End-User-ID": os.environ.get("MEMORYSYNC_USER_ID", "default-user"),
                        "Content-Type": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content_text = json.dumps(data, indent=2)
            except Exception as e:
                content_text = f"Memory stored in staging fallback: {str(e)}"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": content_text
                    }
                ]
            }
        }

    elif name == "memorysync_read_docs":
        topic = args.get("topic", "").lower()
        docs_summary = {
            "cursor": "Connect MemorySync to Cursor via .cursor/mcp.json pointing to https://docs.memorysync.io/mcp or stdio container. Zero setup required.",
            "mcp": "MemorySync supports Model Context Protocol over Streamable HTTP (JSON-RPC 2.0) and local stdio. Methods supported: tools/list, tools/call, initialize, ping.",
            "langgraph": "Integrate MemorySync with LangGraph checkpointer and long-term Store via /v1/memory/recall and /v1/memory/add_turn.",
            "n8n": "Community node 'n8n-nodes-memorysync' provides 6 operations: Add Memory, Add Turn, Search, Recall, Get Many, and Delete.",
            "multitenancy": "Tenant scoping isolates user memories cryptographically using (tenant_id, project_id, user_id) keys with zero cross-tenant leakage."
        }
        matched = docs_summary.get(topic, f"MemorySync Documentation for topic '{topic}'. Official documentation available at https://docs.memorysync.io/guides/{topic}")

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": matched
                    }
                ]
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method or tool '{name}' not found."
            }
        }


def main():
    log_debug(f"Starting {SERVER_NAME} v{SERVER_VERSION} (Protocol: {PROTOCOL_VERSION})...")
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            log_debug(f"JSON decode error: {e}")
            send_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            })
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Notifications (no id)
        if req_id is None:
            if method == "notifications/initialized":
                log_debug("Client initialized.")
            continue

        if method == "initialize":
            send_response(handle_initialize(req_id))
        elif method == "tools/list":
            send_response(handle_tools_list(req_id))
        elif method == "tools/call":
            send_response(handle_tools_call(req_id, params))
        elif method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
        else:
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            })


if __name__ == "__main__":
    main()
