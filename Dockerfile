# MemorySync MCP Server — deployable image
#
# This is the image registries and hosts build: a minimal container that speaks
# JSON-RPC 2.0 over stdio and nothing else. Keep it that way. Every extra
# package here widens the security-scan surface and slows the build for an
# entry point that only needs the Python standard library.
#
# Looking for the developer sandbox with bash, curl, jq and Node for running
# tools/inspect_memory.sh and the examples? That is Dockerfile.dev, which is
# what docker-compose.yml builds.

FROM python:3.12-slim

# Unbuffered stdio is required, not cosmetic: an MCP client reads responses off
# stdout synchronously, so a buffered stream makes the server look unresponsive.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Defaults are the public endpoints. Override MEMORYSYNC_API_KEY at runtime to
# enable the memory tools; the docs tool needs no credentials.
ENV MEMORYSYNC_API_URL=https://api.memorysync.io \
    MEMORYSYNC_DOCS_MCP_URL=https://docs.memorysync.io/mcp

WORKDIR /app

# Copy only what the package build needs, so edits to docs or examples do not
# invalidate this layer.
COPY pyproject.toml README.md LICENSE server.py ./

RUN pip install --no-cache-dir .

# Run unprivileged. The server makes outbound HTTPS calls and reads env vars; it
# has no reason to hold root.
RUN useradd --create-home --uid 10001 mcp
USER mcp

# Installed console script from [project.scripts] in pyproject.toml.
ENTRYPOINT ["memorysync-mcp"]
