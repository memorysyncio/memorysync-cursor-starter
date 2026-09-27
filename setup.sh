#!/usr/bin/env bash
# ==============================================================================
# MemorySync Cursor Starter - Automated Setup Script (macOS / Linux)
# Connects Cursor to MemorySync Model Context Protocol (MCP) in 1 click.
# ==============================================================================

set -eo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}=== MemorySync Cursor Starter Setup ===${RESET}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_DIR="${SCRIPT_DIR}/.cursor"
MCP_CONFIG="${CURSOR_DIR}/mcp.json"

# Ensure .cursor directory exists
mkdir -p "${CURSOR_DIR}"

# Create or verify .cursor/mcp.json
if [[ -f "${MCP_CONFIG}" ]]; then
    echo -e "${YELLOW}Notice:${RESET} Found existing ${MCP_CONFIG}."
else
    echo -e "${CYAN}==>${RESET} Creating project-scoped MCP configuration at ${MCP_CONFIG}..."
    cat << 'EOF' > "${MCP_CONFIG}"
{
  "mcpServers": {
    "memorysync": {
      "url": "https://mcp.memorysync.io/mcp"
    },
    "memorysync-docs": {
      "url": "https://docs.memorysync.io/mcp"
    }
  }
}
EOF
    echo -e "${GREEN}✓ Created .cursor/mcp.json${RESET}"
fi

# Ensure tools are executable
if [[ -f "${SCRIPT_DIR}/tools/inspect_memory.sh" ]]; then
    chmod +x "${SCRIPT_DIR}/tools/inspect_memory.sh"
    echo -e "${GREEN}✓ Made tools/inspect_memory.sh executable${RESET}"
fi

# Test API connection
echo -e "\n${CYAN}==>${RESET} Verifying live MCP endpoint connectivity..."
if command -v curl >/dev/null 2>&1; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://docs.memorysync.io/mcp || echo "000")
    if [[ "$STATUS" == "200" || "$STATUS" == "405" ]]; then
        echo -e "${GREEN}✓ MemorySync Docs MCP Endpoint is online and reachable.${RESET}"
    else
        echo -e "${YELLOW}! MCP endpoint returned HTTP ${STATUS}. Please verify internet access.${RESET}"
    fi
fi

echo -e "\n${BOLD}${GREEN}Setup Complete!${RESET}"
echo -e "To start using MemorySync in Cursor:"
echo -e "1. Open this repository in Cursor."
echo -e "2. Cursor will automatically detect ${BOLD}.cursor/mcp.json${RESET} and ${BOLD}.cursorrules${RESET}."
echo -e "3. Open Cursor Composer (${BOLD}Cmd+I${RESET}) and type: ${CYAN}\"Check our saved architecture rules in MemorySync\"${RESET}."
echo -e "4. Optional: Inspect saved memories directly in terminal via ${BOLD}./tools/inspect_memory.sh ping${RESET}.\n"
