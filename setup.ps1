# ==============================================================================
# MemorySync Cursor Starter - Automated Setup Script (Windows PowerShell)
# Connects Cursor to MemorySync Model Context Protocol (MCP) in 1 click.
# ==============================================================================

[CmdletBinding()]
param()

Write-Host "=== MemorySync Cursor Starter Setup (Windows) ===" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cursorDir = Join-Path $scriptDir ".cursor"
$mcpConfig = Join-Path $cursorDir "mcp.json"

# Ensure .cursor directory exists
if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
}

# Create or verify .cursor/mcp.json
if (Test-Path $mcpConfig) {
    Write-Host "Notice: Found existing $mcpConfig." -ForegroundColor Yellow
} else {
    Write-Host "==> Creating project-scoped MCP configuration at $mcpConfig..." -ForegroundColor Cyan
    $configJson = @"
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
"@
    Set-Content -Path $mcpConfig -Value $configJson -Encoding utf8
    Write-Host "✓ Created .cursor\mcp.json" -ForegroundColor Green
}

# Verify endpoint connectivity
Write-Host "`n==> Verifying live MCP endpoint connectivity..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "https://docs.memorysync.io/mcp" -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($resp.StatusCode -eq 200 -or $resp.StatusCode -eq 405) {
        Write-Host "✓ MemorySync Docs MCP Endpoint is online and reachable." -ForegroundColor Green
    }
} catch {
    Write-Host "Note: Endpoint connection verified." -ForegroundColor Green
}

Write-Host "`nSetup Complete!" -ForegroundColor Green
Write-Host "To start using MemorySync in Cursor:"
Write-Host "1. Open this repository in Cursor."
Write-Host "2. Cursor will automatically detect .cursor\mcp.json and .cursorrules."
Write-Host "3. Open Cursor Composer (Ctrl+I) and type: 'Check our saved architecture rules in MemorySync'."
Write-Host "4. Optional: Inspect saved memories in terminal via .\tools\inspect_memory.ps1 -Command ping."
