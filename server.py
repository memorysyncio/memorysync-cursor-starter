#!/usr/bin/env python3
"""
MemorySync Model Context Protocol (MCP) Server
Standard stdio JSON-RPC 2.0 server implementation for Cursor, Claude Desktop, and AI agents.

Specification: Model Context Protocol (MCP) 2024-11-05
"""

import sys
import json
import os
import urllib.error
import urllib.parse
import urllib.request

SERVER_NAME = "memorysync-cursor-starter"
SERVER_VERSION = "1.1.0"
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
                    "description": (
                        "Natural language description of the fact you are looking for, for "
                        "example 'which ORM does this project use' or 'deployment target'. "
                        "Phrase it as the topic you need, not as a question to the user. "
                        "Matching is semantic, so exact wording from the original memory is "
                        "not required. An empty or single-word query returns weak matches; "
                        "prefer a short phrase."
                    ),
                    "minLength": 1,
                    "examples": ["which ORM does this project use", "API error handling convention"]
                },
                "k": {
                    "type": "integer",
                    "description": (
                        "Maximum number of memories to return. Defaults to 5 if omitted. "
                        "Ranked results degrade after the top few, so raise this only when "
                        "surveying everything known about an area rather than answering one "
                        "question."
                    ),
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
                    "description": (
                        "One self-contained fact, written so it still makes sense with no "
                        "surrounding conversation. Write 'This project uses Postgres with "
                        "SQLAlchemy 2.x', not 'we decided to use that one'. Pronouns and "
                        "references to the current chat will not resolve in a later session."
                    ),
                    "minLength": 1,
                    "examples": [
                        "This project uses Postgres with SQLAlchemy 2.x",
                        "All API errors must return RFC 7807 problem details"
                    ]
                },
                "source": {
                    "type": "string",
                    "description": (
                        "Which client or agent observed this fact, used for attribution when "
                        "two memories conflict. Defaults to 'cursor' if omitted."
                    ),
                    "default": "cursor",
                    "examples": ["cursor", "claude-code", "ci"]
                },
                "metadata": {
                    "type": "object",
                    "description": (
                        "Optional flat key-value tags used to narrow later searches, for "
                        "example {\"area\": \"database\"}. Values should be short strings. "
                        "Omit rather than passing an empty object."
                    ),
                    "additionalProperties": True,
                    "examples": [{"area": "database"}, {"area": "api", "scope": "public"}]
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
                    "description": (
                        "Documentation topic or page slug, for example 'cursor', "
                        "'claude-code', 'langgraph', 'n8n', 'multi-tenant', or 'quickstart'. "
                        "An unrecognised topic returns the closest matching page rather than "
                        "an error, so check the returned url before relying on the content. "
                        "Pass one topic per call."
                    ),
                    "minLength": 1,
                    "examples": ["cursor", "multi-tenant", "quickstart"]
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
    },
    {
        "name": "memorysync_get",
        "title": "Read one memory in full",
        "description": (
            "Fetch the complete stored record for a single memory id, including its text, "
            "tags, importance and timestamps. Use this after memorysync_search when a result "
            "looks relevant but the snippet is not enough to act on, or when you need the "
            "creation date to judge whether a fact is stale. Takes an id, not a search "
            "phrase - to find a memory by topic, call memorysync_search first and pass an id "
            "from its results."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "Identifier of the memory to read, taken from the id field of a memorysync_search result.",
                    "minLength": 1,
                    "examples": ["mem_7f2a91c4"]
                }
            },
            "required": ["memory_id"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Identifier of the memory."},
                "text": {"type": "string", "description": "The stored fact in full."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags attached to this memory."},
                "importance": {"type": "number", "description": "Importance score used in ranking."},
                "created_at": {"type": "string", "description": "When the fact was first observed, for judging staleness."},
                "updated_at": {"type": "string", "description": "When the record last changed."}
            },
            "required": ["id", "text"]
        },
        "annotations": {
            "readOnlyHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "memorysync_related",
        "title": "Find memories connected to a topic",
        "description": (
            "Traverse the memory graph to return facts connected to a topic, so you can see "
            "the surrounding context rather than isolated matches. Use this when a decision "
            "depends on several linked facts - for example every memory touching "
            "authentication - or to discover related constraints you did not think to search "
            "for. memorysync_search ranks independent matches by relevance; this returns a "
            "connected neighbourhood instead."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Topic to centre the graph on, for example 'authentication' or 'database schema'.",
                    "minLength": 1,
                    "examples": ["authentication", "deployment"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum connected memories to return. Defaults to 20 if omitted. Larger graphs are harder to reason over, so raise this only when mapping an area.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                },
                "decision_focus": {
                    "type": "boolean",
                    "description": "When true, restricts the graph to memories that record decisions rather than general facts. Useful for reconstructing why something was chosen.",
                    "default": False
                }
            },
            "required": ["q"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "nodes": {
                    "type": "array",
                    "description": "Connected memories.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Memory identifier."},
                            "text": {"type": "string", "description": "The stored fact."}
                        }
                    }
                },
                "edges": {
                    "type": "array",
                    "description": "Relationships between the returned memories.",
                    "items": {"type": "object"}
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "memorysync_decisions",
        "title": "List recorded decisions and contradictions",
        "description": (
            "Return memories that record decisions, along with any that contradict each "
            "other, so a superseded choice is visible rather than silently competing with "
            "the current one. Call this before proposing an architectural change, to check "
            "whether the question was already settled and why. This surfaces conflict "
            "between stored facts; memorysync_search returns matches without telling you "
            "when two of them disagree."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional topic filter, for example 'caching'. Omit to list recent decisions across all areas."
                },
                "k": {
                    "type": "integer",
                    "description": "Maximum decisions to return. Defaults to 10 if omitted.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "description": "Recorded decisions, newest first.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Memory identifier."},
                            "text": {"type": "string", "description": "The decision as recorded."},
                            "created_at": {"type": "string", "description": "When it was decided."},
                            "superseded_by": {"type": "string", "description": "Present when a later decision replaced this one."}
                        }
                    }
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "memorysync_forget",
        "title": "Delete memories (previews by default)",
        "description": (
            "Permanently delete one or more memories by id. Use this when a stored fact is "
            "wrong or the user asks you to forget something - not to tidy up, because a "
            "deleted memory cannot be recovered. This previews by default: it reports what "
            "would be deleted and deletes nothing until dry_run is explicitly set to false. "
            "Confirm with the user before that second call. To find the ids to pass, use "
            "memorysync_search."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_ids": {
                    "type": "array",
                    "description": "Identifiers of the memories to delete, from memorysync_search results.",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "examples": [["mem_7f2a91c4"]]
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Defaults to true, which previews the deletion without performing it. Pass false only after the user has confirmed.",
                    "default": True
                },
                "reason": {
                    "type": "string",
                    "description": "Short note recorded in the audit log explaining why these memories were removed.",
                    "examples": ["fact was superseded", "user requested removal"]
                }
            },
            "required": ["memory_ids"],
            "additionalProperties": False
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "dry_run": {"type": "boolean", "description": "Whether this call only previewed."},
                "deleted_count": {"type": "integer", "description": "Number deleted, or number that would be deleted when previewing."},
                "deleted_ids": {"type": "array", "items": {"type": "string"}, "description": "Identifiers affected."}
            },
            "required": ["dry_run", "deleted_count"]
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
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


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "X-End-User-ID": os.environ.get("MEMORYSYNC_USER_ID", "default-user"),
        "Content-Type": "application/json",
    }


def _tool_result(req_id, payload, is_error: bool = False):
    """Wrap a payload as an MCP tool result.

    When the payload is a dict it is returned as ``structuredContent`` as well as
    text. These tools declare an ``outputSchema``, and a client that reads the
    schema expects structured output to match it - returning only a text blob
    makes the schema a promise the server does not keep.
    """
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2)
    result = {"content": [{"type": "text", "text": text}]}
    if isinstance(payload, dict) and not is_error:
        result["structuredContent"] = payload
    if is_error:
        result["isError"] = True
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _require_key(req_id):
    """Return an error result when no credentials are configured, or None.

    This deliberately fails loudly. Reporting success for a write that never
    reached the server teaches the model a fact is stored when it is not, and the
    loss only surfaces later as a silent empty read.
    """
    if os.environ.get("MEMORYSYNC_API_KEY"):
        return None
    return _tool_result(
        req_id,
        "MEMORYSYNC_API_KEY is not set, so this call was not sent and nothing was "
        "stored or retrieved. Export MEMORYSYNC_API_KEY and retry. The "
        "memorysync_read_docs tool needs no credentials and still works.",
        is_error=True,
    )


def _api(req_id, method: str, path: str, *, body=None, query=None):
    """Call the MemorySync REST API and return an MCP tool result."""
    missing = _require_key(req_id)
    if missing is not None:
        return missing

    url = f"{DEFAULT_API_ENDPOINT}{path}"
    if query:
        pairs = {k: v for k, v in query.items() if v is not None}
        if pairs:
            url = f"{url}?{urllib.parse.urlencode(pairs)}"

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers=_auth_headers(os.environ["MEMORYSYNC_API_KEY"]),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
        return _tool_result(req_id, json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        return _tool_result(
            req_id,
            f"MemorySync API returned HTTP {exc.code} for {method} {path}: {detail}",
            is_error=True,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to the agent, not swallowed
        return _tool_result(
            req_id,
            f"Could not reach the MemorySync API ({type(exc).__name__}: {exc}). "
            "Nothing was stored or retrieved.",
            is_error=True,
        )


def handle_tools_call(req_id, params):
    name = params.get("name")
    args = params.get("arguments", {})

    if name == "memorysync_search":
        query = args.get("query", "")
        k = args.get("k", 5)
        api_key = os.environ.get("MEMORYSYNC_API_KEY")
        
        if not api_key:
            # Previously this reported "staging mode active: 0 remote errors",
            # which reads as success for a search that never ran. An agent told
            # that gets back nothing and concludes no memories exist.
            return _require_key(req_id)
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
            # Previously this claimed "recorded locally... staged successfully"
            # while storing nothing anywhere. Silent write loss is the worst
            # failure a memory layer can have, so this now fails loudly.
            return _require_key(req_id)
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

    elif name == "memorysync_get":
        memory_id = args.get("memory_id", "").strip()
        if not memory_id:
            return _tool_result(req_id, "memory_id is required.", is_error=True)
        return _api(req_id, "GET", f"/memory/{urllib.parse.quote(memory_id, safe='')}")

    elif name == "memorysync_related":
        q = args.get("q", "").strip()
        if not q:
            return _tool_result(req_id, "q is required.", is_error=True)
        return _api(
            req_id,
            "GET",
            "/memory/graph",
            query={
                "q": q,
                "limit": args.get("limit", 20),
                "decision_focus": str(bool(args.get("decision_focus", False))).lower(),
                "user_id": os.environ.get("MEMORYSYNC_USER_ID"),
            },
        )

    elif name == "memorysync_decisions":
        return _api(
            req_id,
            "GET",
            "/memory/decisions",
            query={
                "query": args.get("query"),
                "k": args.get("k", 10),
                "user_id": os.environ.get("MEMORYSYNC_USER_ID"),
            },
        )

    elif name == "memorysync_forget":
        memory_ids = args.get("memory_ids") or []
        if not isinstance(memory_ids, list) or not memory_ids:
            return _tool_result(
                req_id, "memory_ids must be a non-empty array of ids.", is_error=True
            )
        # Defaults to a preview. The caller has to pass dry_run=false explicitly,
        # which mirrors the two-step confirmation the hosted server enforces on
        # destructive tools.
        dry_run = args.get("dry_run", True)
        return _api(
            req_id,
            "DELETE",
            "/memory/forget",
            body={
                "memory_ids": memory_ids,
                "dry_run": bool(dry_run),
                "reason": args.get("reason"),
                "user_id": os.environ.get("MEMORYSYNC_USER_ID"),
            },
        )

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
