# Multi-Device Sync

Target devices:

- Windows home
- Windows work
- Mac mobile

Use Git as the source of truth for this research workspace. Each device should clone the same private repository into its local research folder. Do not put this Git repository inside a cloud drive auto-sync folder.

## One-Time Setup On First Device

```powershell
git init
git branch -M main
git lfs install
git add .
git commit -m "Initialize research workspace"
git remote add origin <private-repo-url>
git push -u origin main
```

## One-Time Setup On Other Windows Devices

```powershell
git clone <private-repo-url> E:\Research\reserach
cd E:\Research\reserach
git lfs install
```

If the target path differs, keep the path in your personal workspace index.

## One-Time Setup On Mac

```bash
git clone <private-repo-url> ~/Research/reserach
cd ~/Research/reserach
git lfs install
```

## Start Work

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_start.ps1
```

On Mac:

```bash
bash scripts/sync_start.sh
```

This pulls remote changes with rebase and shows the local status.

## Finish Work

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_finish.ps1 -Message "your commit message"
```

On Mac:

```bash
bash scripts/sync_finish.sh "your commit message"
```

This checks ignored-sensitive files, stages allowed changes, commits them, and pushes when a remote exists.

## Conflict Rule

Before switching devices, always finish with a clean `git status`. If two devices edited the same Markdown file, pull first and resolve the conflict immediately on the device where you notice it.
