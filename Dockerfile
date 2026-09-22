# MemorySync Cursor Starter Container
# Provides an isolated staging environment with Node.js, Python, and MCP inspection tools

FROM node:20-slim

# Install Python, curl, bash, git, and jq
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    bash \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Set default environment variables
ENV MEMORYSYNC_MCP_URL=https://mcp.memorysync.io/mcp
ENV MEMORYSYNC_DOCS_MCP_URL=https://docs.memorysync.io/mcp
ENV PYTHONUNBUFFERED=1

# Copy starter project files
COPY . /workspace

# Make scripts executable
RUN chmod +x setup.sh tools/inspect_memory.sh 2>/dev/null || true

# Default command runs the MCP stdio server
CMD ["python3", "server.py"]
