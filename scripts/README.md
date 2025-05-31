# QuantFlow Maintenance Scripts

This directory contains automated maintenance scripts to keep the QuantFlow repository clean and organized.

## Scripts Available

### 1. maintenance.py
**Python-based maintenance script with full features**

```bash
# Basic cleanup (dry run to see what would be changed)
python scripts/maintenance.py --dry-run

# Perform cleanup and commit changes
python scripts/maintenance.py

# Cleanup, commit, and push to GitHub
python scripts/maintenance.py --push
```

**Features:**
- Removes `__pycache__` directories
- Cleans temporary files (*.pyc, *.pyo, *.tmp, *.log, .DS_Store, Thumbs.db)
- Removes empty directories
- Creates detailed commit messages
- Supports dry-run mode
- Optional automatic push to remote

### 2. maintenance.ps1
**PowerShell script for Windows users**

```powershell
# Basic cleanup
.\scripts\maintenance.ps1

# Cleanup and push changes
.\scripts\maintenance.ps1 -Push

# Dry run to see what would be changed
.\scripts\maintenance.ps1 -DryRun
```

**Features:**
- Removes `__pycache__` directories
- Cleans temporary files
- Automatic git commit with timestamp
- Optional push to remote
- Colored output for better visibility

### 3. maintenance.bat
**Simple batch file for easy Windows execution**

```cmd
# Double-click to run, or from command line:
scripts\maintenance.bat
```

**Features:**
- Easy double-click execution
- Automatically calls the PowerShell script
- Provides user feedback
- Pauses for user confirmation

## Recommended Usage

### Daily/Weekly Maintenance
Run the basic cleanup regularly:
```bash
python scripts/maintenance.py
```

### Before Important Commits
Clean up and verify with dry-run first:
```bash
python scripts/maintenance.py --dry-run
python scripts/maintenance.py --push
```

### Automated Maintenance
You can set up these scripts to run automatically using:

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Set to run weekly
4. Action: Start a program
5. Program: `powershell.exe`
6. Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\QuantFlow\scripts\maintenance.ps1" -Push`

**GitHub Actions (Recommended):**
Add a workflow file to automatically run maintenance:

```yaml
# .github/workflows/maintenance.yml
name: Repository Maintenance
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  maintenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Run maintenance
        run: python scripts/maintenance.py --push
```

## What Gets Cleaned

### Always Removed:
- `__pycache__/` directories and contents
- `*.pyc`, `*.pyo` compiled Python files
- `*.tmp`, `*.temp` temporary files
- `*.log` log files (except in protected directories)
- `.DS_Store` (macOS metadata)
- `Thumbs.db` (Windows thumbnails)

### Protected Directories:
- `.git/` (version control)
- `.venv/`, `venv/` (virtual environments)
- `node_modules/` (Node.js dependencies)
- Configuration and data directories

## Troubleshooting

### Permission Errors
If you get permission errors, run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Git Authentication
For automatic pushing, ensure your git credentials are configured:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Large Repository
For repositories with many files, the Python script provides better progress reporting and error handling.

## Configuration

The scripts respect the `.gitignore` file and will not remove files that should be tracked. The enhanced `.gitignore` includes comprehensive patterns to prevent temporary files from being committed in the first place.
