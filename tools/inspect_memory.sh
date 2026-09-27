#!/usr/bin/env bash
# ==============================================================================
# MemorySync Terminal Inspector
# Single-file zero-dependency curl utility to inspect agent memories from terminal.
# Usage: ./inspect_memory.sh [options] <command> [arguments]
# ==============================================================================

set -eo pipefail

API_URL="${MEMORYSYNC_API_URL:-https://api.memorysync.io}"
API_KEY="${MEMORYSYNC_API_KEY:-}"
PROJECT_ID="${MEMORYSYNC_PROJECT_ID:-}"
LIMIT=10
VERBOSE=0

# ANSI Colors
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

show_help() {
    cat << EOF
${BOLD}MemorySync Terminal Memory Inspector${RESET}

${BOLD}USAGE:${RESET}
    ./inspect_memory.sh [options] <command> [arguments]

${BOLD}COMMANDS:${RESET}
    ping               Test connection to MemorySync API
    stats              Show knowledge graph and memory telemetry statistics
    decisions          Retrieve stored architectural decisions for the project
    query <text>       Semantically search saved agent memories
    help               Show this help message

${BOLD}OPTIONS:${RESET}
    -k, --key <KEY>         MemorySync API Key (or set \$MEMORYSYNC_API_KEY)
    -u, --url <URL>         Base API URL (default: https://api.memorysync.io)
    -p, --project <ID>      Project ID filter (or set \$MEMORYSYNC_PROJECT_ID)
    -l, --limit <NUM>       Maximum results to display (default: 10)
    -v, --verbose           Show raw HTTP response headers
    -h, --help              Show this help menu

${BOLD}EXAMPLES:${RESET}
    export MEMORYSYNC_API_KEY="ms_live_..."
    ./inspect_memory.sh ping
    ./inspect_memory.sh stats
    ./inspect_memory.sh decisions
    ./inspect_memory.sh query "PostgreSQL database configuration"
EOF
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -k|--key)
            API_KEY="$2"
            shift 2
            ;;
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-stats}"
ARG="${2:-}"

# Check API key if not ping
if [[ "$COMMAND" != "ping" && "$COMMAND" != "help" && -z "$API_KEY" ]]; then
    echo -e "${RED}Error:${RESET} MEMORYSYNC_API_KEY is required. Pass via -k or export MEMORYSYNC_API_KEY." >&2
    exit 1
fi

AUTH_HEADER="Authorization: Bearer ${API_KEY}"
CONTENT_HEADER="Content-Type: application/json"

# Formatter helper
format_json() {
    if command -v jq >/dev/null 2>&1; then
        jq -C .
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m json.tool
    elif command -v python >/dev/null 2>&1; then
        python -m json.tool
    else
        cat
    fi
}

case "$COMMAND" in
    ping)
        echo -e "${CYAN}==>${RESET} Pinging MemorySync API at ${BOLD}${API_URL}${RESET}..."
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" || echo "000")
        if [[ "$STATUS" == "200" ]]; then
            echo -e "${GREEN}✓ Connection Healthy (HTTP 200 OK)${RESET}"
        else
            echo -e "${YELLOW}API responded with HTTP ${STATUS} (Endpoint reachable)${RESET}"
        fi
        ;;

    stats)
        echo -e "${CYAN}==>${RESET} Fetching memory & knowledge stats..."
        curl -s -f -X GET "${API_URL}/api/v1/knowledge/stats" \
            -H "${AUTH_HEADER}" \
            -H "${CONTENT_HEADER}" | format_json
        ;;

    decisions)
        echo -e "${CYAN}==>${RESET} Fetching saved architectural decisions..."
        URL="${API_URL}/api/v1/decisions"
        if [[ -n "$PROJECT_ID" ]]; then
            URL="${URL}?project_id=${PROJECT_ID}"
        fi
        curl -s -f -X GET "${URL}" \
            -H "${AUTH_HEADER}" \
            -H "${CONTENT_HEADER}" | format_json
        ;;

    query)
        if [[ -z "$ARG" ]]; then
            echo -e "${RED}Error:${RESET} Please specify a search query: ./inspect_memory.sh query <text>" >&2
            exit 1
        fi
        echo -e "${CYAN}==>${RESET} Querying memories for: ${BOLD}\"${ARG}\"${RESET}..."
        PAYLOAD=$(cat <<EOF
{
    "query": "${ARG}",
    "limit": ${LIMIT},
    "project_id": "${PROJECT_ID}"
}
EOF
)
        curl -s -f -X POST "${API_URL}/api/v1/query" \
            -H "${AUTH_HEADER}" \
            -H "${CONTENT_HEADER}" \
            -d "${PAYLOAD}" | format_json
        ;;

    help)
        show_help
        ;;

    *)
        echo -e "${RED}Unknown command:${RESET} $COMMAND" >&2
        show_help
        exit 1
        ;;
esac
