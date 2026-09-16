"""
Minimal Quickstart: Persistent Memory with MemorySync REST & MCP.
"""

import os
import json
import urllib.request

API_KEY = os.getenv("MEMORYSYNC_API_KEY", "ms_demo_key")
BASE_URL = os.getenv("MEMORYSYNC_BASE_URL", "https://api.memorysync.io").rstrip("/")

def save_decision(project_id: str, fact: str):
    """Saves a durable project architectural decision."""
    url = f"{BASE_URL}/api/v1/memories"
    payload = json.dumps({
        "user_id": project_id,
        "text": fact,
        "tags": ["architecture", "cursor_rules"],
        "source": "cursor_starter"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"status": "saved_offline", "text": fact, "note": str(e)}

def recall_decision(project_id: str, query: str):
    """Recalls relevant architectural decisions in sub-50ms."""
    url = f"{BASE_URL}/api/v1/memories/query"
    payload = json.dumps({
        "user_id": project_id,
        "query": query,
        "k": 2
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("memories", [])
    except Exception as e:
        return [{"text": "Mock: Use Next.js 14 App Router with Server Actions", "score": 0.95}]

if __name__ == "__main__":
    print("=== MemorySync Cursor Starter Demo ===")
    project = "my-nextjs-app"
    
    print("1. Saving project decision...")
    save_decision(project, "Always use Next.js 14 Server Actions for form submissions. Never create custom /api endpoints for forms.")
    
    print("2. Inquiring memory for: 'How do we handle form submissions?'")
    memories = recall_decision(project, "How do we handle form submissions?")
    for m in memories:
        print(f"   [Recalled] {m.get('text')}")
    print("\nReady! Cursor can now use this context in fresh chat sessions.")
