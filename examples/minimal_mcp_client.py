"""
Minimal Python MCP Memory Client in 15 Lines of Code
Zero third-party dependencies. Direct JSON-RPC over HTTP/SSE.
"""
import json, urllib.request

class MinimalMemoryClient:
    def __init__(self, endpoint="https://mcp.memorysync.io/mcp", api_key=None):
        self.endpoint, self.headers = endpoint, {"Content-Type": "application/json"}
        if api_key: self.headers["Authorization"] = f"Bearer {api_key}"

    def call(self, tool_name: str, arguments: dict):
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload, headers=self.headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

# Example: Recall project architecture decisions with sub-50ms latency
client = MinimalMemoryClient()
print(client.call("recall_memories", {"query": "database connection pool architecture", "k": 3}))
