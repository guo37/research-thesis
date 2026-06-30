param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".git")) {
    throw "This folder is not a Git repository yet. Run: git init"
}

$sensitive = Get-ChildItem -Recurse -Force -File -Include "*.pem", "*.key", ".env", ".env.*" |
    Where-Object { $_.FullName -notmatch "\\.git\\" }

if ($sensitive) {
    Write-Host "Sensitive local files found. They are ignored and will not be committed:"
    $sensitive | ForEach-Object { Write-Host " - $($_.FullName)" }
}

git lfs install --local | Out-Null
git add .

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "No staged changes to commit."
    git status --short --branch
    exit 0
}

git commit -m $Message

if (-not $NoPush) {
    $remote = git remote
    if ($remote) {
        git push
    } else {
        Write-Host "No Git remote configured; commit created locally. Add a remote before multi-device sync."
    }
}

git status --short --branch

