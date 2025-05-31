# QuantFlow Repository Maintenance Guide

## Overview

This document outlines the maintenance strategy for the QuantFlow repository to ensure it remains clean, organized, and efficient.

## 🧹 What We Clean Up

### Automatic Cleanup (Every Commit)
The repository maintenance system automatically removes:

- **Python Cache Files**: `__pycache__/` directories and `*.pyc`, `*.pyo` files
- **Temporary Files**: `*.tmp`, `*.temp`, `*~` backup files  
- **Log Files**: `*.log` files (except in protected directories)
- **OS Metadata**: `.DS_Store` (macOS), `Thumbs.db` (Windows)
- **IDE Files**: Temporary editor files, swap files
- **Build Artifacts**: `dist/`, `build/`, `*.egg-info/` directories

### Protected Areas
These directories are never cleaned:
- `.git/` - Version control data
- `.venv/`, `venv/` - Virtual environments  
- `data/` - Important data files
- `config/` - Configuration files
- `docs/` - Documentation

## 🔄 Maintenance Schedule

### Manual Maintenance
- **Before major commits**: Run cleanup to ensure clean repository state
- **Weekly**: Recommended for active development periods
- **Before releases**: Always clean up before tagging versions

### Automated Maintenance
- **GitHub Actions**: Runs every Sunday at 2 AM UTC
- **Local Scripts**: Available for immediate cleanup

## 🛠️ Available Tools

### 1. Quick Cleanup (Windows)
```bash
# Double-click or run from command line:
scripts\maintenance.bat
```

### 2. PowerShell Script
```powershell
# Basic cleanup
.\scripts\maintenance.ps1

# With automatic push to GitHub
.\scripts\maintenance.ps1 -Push

# Preview mode (see what would be cleaned)
.\scripts\maintenance.ps1 -DryRun
```

### 3. Python Script (Most Features)
```bash
# Preview what would be cleaned
python scripts/maintenance.py --dry-run

# Clean and commit locally
python scripts/maintenance.py

# Clean, commit, and push to GitHub
python scripts/maintenance.py --push
```

## 📊 Maintenance History

### 2025-05-31: Initial Cleanup
- **Removed**: 1,920 `__pycache__` directories
- **Cleaned**: Multiple `.DS_Store` files from virtual environment
- **Enhanced**: `.gitignore` with comprehensive patterns
- **Added**: Automated maintenance scripts
- **Result**: Repository size significantly reduced

## 🔧 Configuration

### Enhanced .gitignore
The repository now includes comprehensive `.gitignore` patterns to prevent temporary files from being committed:

```gitignore
# Python
*.pyc
*.pyo
__pycache__/
*.egg-info/
dist/
build/

# OS Files  
.DS_Store
Thumbs.db

# IDE Files
.vscode/
.idea/
*.swp

# Logs & Temp
*.log
*.tmp
```

### Git Hooks (Optional)
You can set up pre-commit hooks to automatically clean before each commit:

```bash
# Create pre-commit hook
echo '#!/bin/bash\npython scripts/maintenance.py' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## 📈 Benefits

### Performance Improvements
- **Faster Git Operations**: Fewer files to track and index
- **Reduced Clone Time**: Smaller repository size
- **Better IDE Performance**: Less clutter in file explorers

### Development Quality
- **Cleaner Commits**: Only relevant code changes
- **Easier Code Review**: No noise from temporary files
- **Professional Appearance**: Clean repository structure

### Storage Efficiency
- **GitHub Storage**: Reduced repository size
- **Local Storage**: Less disk space usage
- **Backup Efficiency**: Faster backups with fewer files

## 🚀 Best Practices

### For Developers
1. **Run cleanup before major commits**
2. **Use dry-run mode first** to preview changes
3. **Review .gitignore regularly** for new file patterns
4. **Don't commit IDE settings** unless team-agreed

### For Team Leads
1. **Schedule regular maintenance** using GitHub Actions
2. **Monitor repository size** trends
3. **Update maintenance scripts** as project evolves
4. **Document any special requirements** in this file

### For CI/CD
1. **Include cleanup in build pipelines**
2. **Verify clean state** before deployments
3. **Alert on unusual file patterns**
4. **Automate maintenance reporting**

## 🔍 Monitoring

### Repository Health Checks
- **File Count**: Monitor total number of files
- **Repository Size**: Track growth patterns  
- **Temporary Files**: Alert on accumulation
- **Build Artifacts**: Ensure proper cleanup

### Maintenance Reports
The automated maintenance creates reports showing:
- Number of files cleaned
- Types of files removed
- Repository size before/after
- Any errors or warnings

## 📞 Support

### Troubleshooting
- **Permission Errors**: Run PowerShell as Administrator
- **Git Issues**: Ensure proper authentication setup
- **Script Errors**: Check Python/PowerShell versions

### Getting Help
- Check `scripts/README.md` for detailed usage
- Review GitHub Actions logs for automated runs
- Contact repository maintainers for issues

---

*Last Updated: 2025-05-31*  
*Maintained by: QuantFlow Development Team*
