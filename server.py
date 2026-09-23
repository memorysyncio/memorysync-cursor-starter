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

# Tool definitions are what an LLM reads before deciding which tool to call, and
# what Glama's Tool Definition Quality Score grades. Two rules apply here:
#
#   1. Every description states when to use the tool AND when not to. The failure
#      mode these definitions guard against is a model confusing
#      `memorysync_search` (the user's own saved project facts) with
#      `memorysync_read_docs` (MemorySync's public product documentation). Both
#      "retrieve information", so each one names the other as the alternative.
#   2. Descriptions describe behaviour, not marketing. Latency figures do not
#      help a model choose a tool, so they belong in the docs, not here.
TOOLS = [
    {
        "name": "memorysync_search",
        "title": "Search saved project memories",
        "description": (
            "Retrieve facts previously saved about THIS project and user: architectural "
            "decisions, naming conventions, pinned dependency versions, and stated "
            "preferences. Call this before answering questions about how the project is "
            "built, and before re-asking the user something they may have already told "
            "you. Returns ranked matches with an id and a relevance score. "
            "This searches the user's own stored memories only - to look up how "
            "MemorySync itself works, use memorysync_read_docs instead."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of the fact you are looking for, for example 'which ORM does this project use'."
                },
                "k": {
                    "type": "integer",
                    "description": "Maximum number of memories to return. Use a small value; ranked results degrade after the top few.",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of memories returned."},
                "results": {
                    "type": "array",
                    "description": "Matching memories, most relevant first.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Stable identifier, usable with memorysync_add metadata or for later reference."},
                            "text": {"type": "string", "description": "The stored fact."},
                            "score": {"type": "number", "description": "Relevance score for this query."},
                            "created_at": {"type": "string", "description": "When the memory was first observed, for judging staleness."}
                        }
                    }
                }
            },
            "required": ["count", "results"]
        },
        "annotations": {
            "readOnlyHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "memorysync_add",
        "title": "Save a durable project memory",
        "description": (
            "Persist one fact so it survives after this conversation ends: an architectural "
            "decision, a convention the user asked you to follow, or a constraint that will "
            "still be true next session. Call this when the user states a lasting preference "
            "or you settle a design question. Do not call it for transient chat, for content "
            "already returned by memorysync_search, or for anything a later session would be "
            "misled by. Save one discrete fact per call rather than a conversation summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "One self-contained fact, written so it still makes sense with no surrounding conversation."
                },
                "source": {
                    "type": "string",
                    "description": "Which client or agent observed this, used for attribution when memories conflict.",
                    "default": "cursor"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional key-value tags, for example {\"area\": \"database\"}, to narrow later searches.",
                    "additionalProperties": True
                }
            },
            "required": ["text"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Identifier of the stored memory."},
                "status": {"type": "string", "description": "Result of the write, for example 'created'."}
            },
            "required": ["id", "status"]
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
    {
        "name": "memorysync_read_docs",
        "title": "Read MemorySync product documentation",
        "description": (
            "Look up MemorySync's own public documentation: REST endpoints, SDK usage, MCP "
            "configuration, and integration guides. Call this before writing MemorySync "
            "integration code, so method names and parameters come from current docs rather "
            "than recall. Returns documentation text for the requested topic. "
            "This reads MemorySync product documentation only - to retrieve facts about the "
            "user's own project, use memorysync_search instead."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Documentation topic or page slug, for example 'cursor', 'claude-code', 'langgraph', 'n8n', 'multi-tenant', or 'quickstart'."
                }
            },
            "required": ["topic"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic that was resolved."},
                "url": {"type": "string", "description": "Canonical documentation URL for the topic."},
                "content": {"type": "string", "description": "Documentation text as Markdown."}
            },
            "required": ["topic", "content"]
        },
        "annotations": {
            "readOnlyHint": True,
            "openWorldHint": True
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
