#!/usr/bin/env python3
"""
QuantFlow Repository Maintenance Script

This script performs routine maintenance tasks:
1. Cleans up temporary files
2. Removes cache directories
3. Commits maintenance changes to git
4. Optionally pushes to remote repository

Usage:
    python scripts/maintenance.py [--push] [--dry-run]
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class RepositoryMaintenance:
    def __init__(self, repo_path: str, dry_run: bool = False):
        self.repo_path = Path(repo_path)
        self.dry_run = dry_run
        self.changes_made = []
        
    def log(self, message: str):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run_git_command(self, command: list) -> tuple:
        """Run a git command and return result"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
            
    def clean_pycache(self):
        """Remove all __pycache__ directories"""
        pycache_dirs = list(self.repo_path.rglob("__pycache__"))
        if pycache_dirs:
            self.log(f"Found {len(pycache_dirs)} __pycache__ directories")
            if not self.dry_run:
                for cache_dir in pycache_dirs:
                    shutil.rmtree(cache_dir, ignore_errors=True)
                self.changes_made.append(f"Removed {len(pycache_dirs)} __pycache__ directories")
            else:
                self.log("DRY RUN: Would remove __pycache__ directories")
        else:
            self.log("No __pycache__ directories found")
            
    def clean_temp_files(self):
        """Remove temporary files"""
        temp_patterns = ["*.pyc", "*.pyo", "*.tmp", "*.log", ".DS_Store", "Thumbs.db"]
        temp_files = []
        
        for pattern in temp_patterns:
            temp_files.extend(self.repo_path.rglob(pattern))
            
        if temp_files:
            self.log(f"Found {len(temp_files)} temporary files")
            if not self.dry_run:
                for temp_file in temp_files:
                    try:
                        temp_file.unlink()
                    except (OSError, PermissionError):
                        pass
                self.changes_made.append(f"Removed {len(temp_files)} temporary files")
            else:
                self.log("DRY RUN: Would remove temporary files")
        else:
            self.log("No temporary files found")
            
    def clean_empty_dirs(self):
        """Remove empty directories (excluding .git and important directories)"""
        important_dirs = {".git", ".venv", "venv", "node_modules"}
        empty_dirs = []
        
        for dirpath in self.repo_path.rglob("*"):
            if (dirpath.is_dir() and 
                not any(dirpath.iterdir()) and 
                dirpath.name not in important_dirs and
                not any(important in str(dirpath) for important in important_dirs)):
                empty_dirs.append(dirpath)
                
        if empty_dirs:
            self.log(f"Found {len(empty_dirs)} empty directories")
            if not self.dry_run:
                for empty_dir in empty_dirs:
                    try:
                        empty_dir.rmdir()
                    except OSError:
                        pass
                self.changes_made.append(f"Removed {len(empty_dirs)} empty directories")
            else:
                self.log("DRY RUN: Would remove empty directories")
        else:
            self.log("No empty directories found")
            
    def check_git_status(self):
        """Check if there are any changes to commit"""
        success, output = self.run_git_command(["status", "--porcelain"])
        if success:
            return bool(output.strip())
        return False
        
    def commit_changes(self, push: bool = False):
        """Commit maintenance changes"""
        if not self.changes_made:
            self.log("No changes to commit")
            return True
            
        if self.dry_run:
            self.log("DRY RUN: Would commit changes")
            return True
            
        # Check if there are actually changes in git
        if not self.check_git_status():
            self.log("No git changes detected")
            return True
            
        # Create commit message
        commit_msg = f"Automated maintenance: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        commit_msg += "\n".join(f"- {change}" for change in self.changes_made)
        
        # Add all changes
        success, output = self.run_git_command(["add", "."])
        if not success:
            self.log(f"Failed to add changes: {output}")
            return False
            
        # Commit changes
        success, output = self.run_git_command(["commit", "-m", commit_msg])
        if not success:
            self.log(f"Failed to commit changes: {output}")
            return False
            
        self.log("Successfully committed maintenance changes")
        
        # Push if requested
        if push:
            success, output = self.run_git_command(["push"])
            if success:
                self.log("Successfully pushed changes to remote")
            else:
                self.log(f"Failed to push changes: {output}")
                return False
                
        return True
        
    def run_maintenance(self, push: bool = False):
        """Run all maintenance tasks"""
        self.log("Starting repository maintenance")
        
        # Clean up files
        self.clean_pycache()
        self.clean_temp_files()
        self.clean_empty_dirs()
        
        # Commit changes
        if self.changes_made or self.dry_run:
            self.commit_changes(push)
        else:
            self.log("Repository is already clean")
            
        self.log("Maintenance completed")


def main():
    parser = argparse.ArgumentParser(description="QuantFlow Repository Maintenance")
    parser.add_argument("--push", action="store_true", help="Push changes to remote repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--repo-path", default=".", help="Path to repository (default: current directory)")
    
    args = parser.parse_args()
    
    # Get absolute path to repository
    repo_path = Path(args.repo_path).resolve()
    
    if not (repo_path / ".git").exists():
        print(f"Error: {repo_path} is not a git repository")
        sys.exit(1)
        
    # Run maintenance
    maintenance = RepositoryMaintenance(str(repo_path), args.dry_run)
    maintenance.run_maintenance(args.push)


if __name__ == "__main__":
    main()
