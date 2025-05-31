# QuantFlow Repository Maintenance Script (PowerShell)
# This script performs routine cleanup and commits changes to git

param(
    [switch]$Push,
    [switch]$DryRun,
    [string]$RepoPath = "."
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor Green
}

function Write-Warning-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red
}

try {
    # Change to repository directory
    $repoFullPath = Resolve-Path $RepoPath
    Set-Location $repoFullPath
    
    Write-Log "Starting repository maintenance for: $repoFullPath"
    
    # Check if this is a git repository
    if (-not (Test-Path ".git")) {
        throw "Not a git repository: $repoFullPath"
    }
    
    $changesMade = @()
    
    # Clean __pycache__ directories
    Write-Log "Checking for __pycache__ directories..."
    $pycacheDirs = Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory -ErrorAction SilentlyContinue
    if ($pycacheDirs) {
        $count = ($pycacheDirs | Measure-Object).Count
        Write-Log "Found $count __pycache__ directories"
        
        if (-not $DryRun) {
            $pycacheDirs | ForEach-Object { 
                Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
            }
            $changesMade += "Removed $count __pycache__ directories"
        } else {
            Write-Log "DRY RUN: Would remove __pycache__ directories"
        }
    } else {
        Write-Log "No __pycache__ directories found"
    }
    
    # Clean temporary files
    Write-Log "Checking for temporary files..."
    $tempFiles = Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo", "*.tmp", "*.log", ".DS_Store", "Thumbs.db" -ErrorAction SilentlyContinue
    if ($tempFiles) {
        $count = ($tempFiles | Measure-Object).Count
        Write-Log "Found $count temporary files"
        
        if (-not $DryRun) {
            $tempFiles | Remove-Item -Force -ErrorAction SilentlyContinue
            $changesMade += "Removed $count temporary files"
        } else {
            Write-Log "DRY RUN: Would remove temporary files"
        }
    } else {
        Write-Log "No temporary files found"
    }
    
    # Check git status
    $gitStatus = git status --porcelain 2>$null
    $hasChanges = $gitStatus -and $gitStatus.Trim()
    
    if ($changesMade.Count -gt 0 -or $DryRun) {
        if ($DryRun) {
            Write-Log "DRY RUN: Would commit maintenance changes"
        } elseif ($hasChanges) {
            # Create commit message
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $commitMsg = "Automated maintenance: $timestamp`n`n"
            $commitMsg += ($changesMade | ForEach-Object { "- $_" }) -join "`n"
            
            # Add and commit changes
            Write-Log "Committing maintenance changes..."
            git add .
            git commit -m $commitMsg
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Successfully committed changes"
                
                # Push if requested
                if ($Push) {
                    Write-Log "Pushing changes to remote..."
                    git push
                    if ($LASTEXITCODE -eq 0) {
                        Write-Log "Successfully pushed to remote"
                    } else {
                        Write-Error-Log "Failed to push changes"
                    }
                }
            } else {
                Write-Error-Log "Failed to commit changes"
            }
        } else {
            Write-Log "No git changes detected"
        }
    } else {
        Write-Log "Repository is already clean"
    }
    
    Write-Log "Maintenance completed successfully"
    
} catch {
    Write-Error-Log $_.Exception.Message
    exit 1
}
