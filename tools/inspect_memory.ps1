<#
.SYNOPSIS
    MemorySync Terminal Inspector for PowerShell
.DESCRIPTION
    Zero-dependency CLI utility to query, inspect, and verify agent memories from the terminal.
.EXAMPLE
    .\inspect_memory.ps1 -Command ping
    .\inspect_memory.ps1 -Command stats -ApiKey "ms_live_..."
    .\inspect_memory.ps1 -Command query -Query "PostgreSQL configuration"
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet("ping", "stats", "decisions", "query", "help")]
    [string]$Command = "stats",

    [Parameter(Position=1)]
    [string]$Query = "",

    [string]$ApiKey = $env:MEMORYSYNC_API_KEY,
    [string]$ApiUrl = $(if ($env:MEMORYSYNC_API_URL) { $env:MEMORYSYNC_API_URL } else { "https://api.memorysync.io" }),
    [string]$ProjectId = $env:MEMORYSYNC_PROJECT_ID,
    [int]$Limit = 10
)

function Show-Usage {
    Write-Host "MemorySync Terminal Memory Inspector (PowerShell)" -ForegroundColor Cyan -NoNewline
    Write-Host "`nUsage: .\inspect_memory.ps1 [-Command] <ping|stats|decisions|query> [[-Query] <text>] [-ApiKey <key>]"
    Write-Host "`nCommands:"
    Write-Host "  ping               Test connection to MemorySync API"
    Write-Host "  stats              Show knowledge graph and memory telemetry statistics"
    Write-Host "  decisions          Retrieve stored architectural decisions for the project"
    Write-Host "  query <text>       Semantically search saved agent memories"
    Write-Host "  help               Show this help message"
}

if ($Command -eq "help") {
    Show-Usage
    exit 0
}

if ($Command -eq "ping") {
    Write-Host "==> Pinging MemorySync API at $ApiUrl..." -ForegroundColor Cyan
    try {
        $resp = Invoke-WebRequest -Uri "$ApiUrl/health" -Method Get -TimeoutSec 10 -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            Write-Host "? Connection Healthy (HTTP 200 OK)" -ForegroundColor Green
        } else {
            Write-Host "API responded with HTTP $($resp.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error connecting to ${ApiUrl}: $_" -ForegroundColor Red
    }
    exit 0
}

if (-not $ApiKey) {
    Write-Host "Error: ApiKey is required. Pass via -ApiKey or set `$env:MEMORYSYNC_API_KEY." -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
}

switch ($Command) {
    "stats" {
        Write-Host "==> Fetching memory & knowledge stats..." -ForegroundColor Cyan
        try {
            $res = Invoke-RestMethod -Uri "$ApiUrl/api/v1/knowledge/stats" -Method Get -Headers $headers -TimeoutSec 15
            $res | ConvertTo-Json -Depth 5
        } catch {
            Write-Host "Failed to fetch stats: $_" -ForegroundColor Red
        }
    }

    "decisions" {
        Write-Host "==> Fetching saved architectural decisions..." -ForegroundColor Cyan
        $url = "$ApiUrl/api/v1/decisions"
        if ($ProjectId) { $url += "?project_id=$ProjectId" }
        try {
            $res = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -TimeoutSec 15
            $res | ConvertTo-Json -Depth 5
        } catch {
            Write-Host "Failed to fetch decisions: $_" -ForegroundColor Red
        }
    }

    "query" {
        if (-not $Query) {
            Write-Host "Error: Query text is required. Example: .\inspect_memory.ps1 -Command query -Query 'database'" -ForegroundColor Red
            exit 1
        }
        Write-Host "==> Querying memories for: `"$Query`"..." -ForegroundColor Cyan
        $body = @{
            query = $Query
            limit = $Limit
            project_id = $ProjectId
        } | ConvertTo-Json

        try {
            $res = Invoke-RestMethod -Uri "$ApiUrl/api/v1/query" -Method Post -Headers $headers -Body $body -TimeoutSec 15
            $res | ConvertTo-Json -Depth 5
        } catch {
            Write-Host "Failed to query memories: $_" -ForegroundColor Red
        }
    }
}
