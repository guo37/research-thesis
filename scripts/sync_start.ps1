param(
    [switch]$NoPull
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".git")) {
    throw "This folder is not a Git repository yet. Run: git init"
}

git lfs install --local | Out-Null

if (-not $NoPull) {
    $remote = git remote
    if ($remote) {
        git pull --rebase --autostash
    } else {
        Write-Host "No Git remote configured; skipping pull."
    }
}

git status --short --branch

