#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Enhanced Commit Push Assistant - AI-Powered Git Automation
Smart script to initialize local Git repository and automatically push to GitHub
with AI-generated commit messages via Langchain + Ollama.

Author: Khalid HAFID-MEDHEB
Date: June 2025
Version: 2.0
"""

import subprocess
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configuration
@dataclass
class Config:
    repo_name: str = "auto-commit-push"
    username: str = "khafidmedheb"
    default_branch: str = "main"
    max_commit_length: int = 72
    use_conventional_commits: bool = True
    ollama_model: str = "mistral"
    
    @property
    def remote_url(self) -> str:
        return f"git@github.com:{self.username}/{self.repo_name}.git"

# Global config instance
config = Config()

class GitOperations:
    """Handles all Git operations with enhanced error handling."""
    
    @staticmethod
    def run_command(command: str, capture_output: bool = True, check: bool = True) -> Optional[str]:
        """Execute system command with enhanced error handling."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output, 
                text=True, 
                check=check,
                encoding='utf-8'
            )
            return result.stdout.strip() if capture_output else None
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(f"❌ Command failed: {command}")
                print(f"   Exit code: {e.returncode}")
                if e.stderr:
                    print(f"   Error: {e.stderr}")
            return None
        except UnicodeDecodeError:
            print(f"⚠️ Encoding issue with command: {command}")
            return None

    @staticmethod
    def is_git_repo() -> bool:
        """Check if current directory is a Git repository."""
        return Path(".git").exists()

    @staticmethod
    def get_repo_status() -> Dict[str, List[str]]:
        """Get comprehensive repository status."""
        status = {
            'untracked': [],
            'modified': [],
            'staged': [],
            'deleted': [],
            'renamed': []
        }
        
        # Get untracked files
        untracked = GitOperations.run_command("git ls-files --others --exclude-standard")
        if untracked:
            status['untracked'] = untracked.split('\n')
        
        # Get modified files
        modified = GitOperations.run_command("git diff --name-only")
        if modified:
            status['modified'] = modified.split('\n')
        
        # Get staged files
        staged = GitOperations.run_command("git diff --cached --name-only")
        if staged:
            status['staged'] = staged.split('\n')
            
        # Get deleted files
        deleted = GitOperations.run_command("git ls-files --deleted")
        if deleted:
            status['deleted'] = deleted.split('\n')
            
        return status

    @staticmethod
    def get_file_changes() -> Dict[str, int]:
        """Get detailed file change statistics."""
        stats = GitOperations.run_command("git diff --numstat")
        if not stats:
            stats = GitOperations.run_command("git diff --cached --numstat")
        
        changes = {'additions': 0, 'deletions': 0, 'files': 0}
        if stats:
            for line in stats.split('\n'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        changes['additions'] += int(parts[0]) if parts[0] != '-' else 0
                        changes['deletions'] += int(parts[1]) if parts[1] != '-' else 0
                        changes['files'] += 1
                    except ValueError:
                        continue
                        
        return changes

    @staticmethod
    def get_recent_commits(limit: int = 5) -> List[str]:
        """Get recent commit messages for context."""
        result = GitOperations.run_command(f"git log --oneline -n {limit}")
        return result.split('\n') if result else []

class CommitMessageGenerator:
    """Enhanced AI-powered commit message generator."""
    
    def __init__(self, model_name: str = "mistral"):
        self.model_name = model_name
        self.conventional_types = {
            'feat': '✨',
            'fix': '🐛', 
            'docs': '📝',
            'style': '🎨',
            'refactor': '♻️',
            'perf': '⚡',
            'test': '✅',
            'build': '🔧',
            'ci': '👷',
            'chore': '🔧',
            'security': '🔒',
            'config': '⚙️'
        }

    def analyze_changes(self, status: Dict[str, List[str]], stats: Dict[str, int]) -> str:
        """Analyze changes to determine commit type and scope."""
        analysis = []
        
        # Determine primary change type
        if any('test' in f.lower() for files in status.values() for f in files):
            analysis.append("test files")
        if any(f.endswith(('.md', '.rst', '.txt')) for files in status.values() for f in files):
            analysis.append("documentation")
        if any(f.endswith(('.json', '.yml', '.yaml', '.toml', '.ini')) for files in status.values() for f in files):
            analysis.append("configuration")
        if any(f.endswith(('.py', '.js', '.ts', '.java', '.cpp')) for files in status.values() for f in files):
            analysis.append("source code")
            
        return ", ".join(analysis) if analysis else "general changes"

    def generate_enhanced_message(self, status: Dict[str, List[str]], stats: Dict[str, int], recent_commits: List[str]) -> Optional[str]:
        """Generate enhanced commit message with better context."""
        try:
            from langchain_ollama import OllamaLLM
            
            # Build comprehensive context
            change_analysis = self.analyze_changes(status, stats)
            files_summary = self._build_files_summary(status)
            context = self._build_context(stats, recent_commits, change_analysis)
            
            # Enhanced prompt for better English commit messages
            prompt = f"""You are a Git commit message expert. Generate a concise, professional commit message in ENGLISH ONLY.

CONTEXT:
{context}

FILES CHANGED:
{files_summary}

REQUIREMENTS:
1. Use conventional commit format: type(scope): description
2. Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, security
3. Max 72 characters total
4. Be specific and descriptive
5. Use present tense, imperative mood
6. NO emojis in the message itself
7. Focus on WHAT changed, not HOW

EXAMPLES:
- feat(auth): add user registration endpoint
- fix(api): resolve null pointer in user validation
- docs(readme): update installation instructions
- refactor(utils): simplify error handling logic

Generate ONE commit message only:"""

            llm = OllamaLLM(model=self.model_name)
            message = llm.invoke(prompt).strip()
            
            # Clean and validate message
            message = self._clean_message(message)
            return message if self._validate_message(message) else None
            
        except ImportError:
            return self._handle_missing_dependency()
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")
            return None

    def _build_files_summary(self, status: Dict[str, List[str]]) -> str:
        """Build a summary of changed files."""
        summary = []
        for change_type, files in status.items():
            if files and files != ['']:
                summary.append(f"{change_type.upper()}: {', '.join(files[:3])}")
                if len(files) > 3:
                    summary.append(f"... and {len(files) - 3} more")
        return '\n'.join(summary) if summary else "No specific files detected"

    def _build_context(self, stats: Dict[str, int], recent_commits: List[str], analysis: str) -> str:
        """Build context for AI prompt."""
        context_parts = [
            f"Change type: {analysis}",
            f"Files modified: {stats['files']}",
            f"Lines added: {stats['additions']}",
            f"Lines deleted: {stats['deletions']}"
        ]
        
        if recent_commits:
            context_parts.append(f"Recent commits: {', '.join(recent_commits[:3])}")
            
        return '\n'.join(context_parts)

    def _clean_message(self, message: str) -> str:
        """Clean and format commit message."""
        # Remove quotes
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        # Remove any prefixes like "Commit message:"
        prefixes = ["commit message:", "message:", "git commit:"]
        for prefix in prefixes:
            if message.lower().startswith(prefix):
                message = message[len(prefix):].strip()
        
        # Ensure proper length
        if len(message) > config.max_commit_length:
            message = message[:config.max_commit_length - 3] + "..."
            
        return message

    def _validate_message(self, message: str) -> bool:
        """Validate commit message format."""
        if not message or len(message) < 10:
            return False
        
        if config.use_conventional_commits:
            # Check for conventional commit format
            return ':' in message and any(msg_type in message.lower() for msg_type in self.conventional_types.keys())
        
        return True

    def _handle_missing_dependency(self) -> Optional[str]:
        """Handle missing langchain-ollama dependency."""
        print("⚠️ langchain-ollama not installed. Installing automatically...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "langchain-ollama"])
            print("✅ langchain-ollama installed successfully!")
            return None  # Will retry in main flow
        except subprocess.CalledProcessError:
            print("❌ Failed to install langchain-ollama")
            return None

    def generate_fallback_message(self, status: Dict[str, List[str]], stats: Dict[str, int]) -> str:
        """Generate fallback message when AI fails."""
        if stats['files'] == 0:
            return "chore: update repository"
        
        # Determine commit type based on files
        commit_type = "feat"
        if any('fix' in f.lower() for files in status.values() for f in files):
            commit_type = "fix"
        elif any(f.endswith('.md') for files in status.values() for f in files):
            commit_type = "docs"
        elif any('test' in f.lower() for files in status.values() for f in files):
            commit_type = "test"
        
        scope = ""
        if stats['files'] == 1:
            # Try to extract scope from single file
            all_files = [f for files in status.values() for f in files if f]
            if all_files:
                filename = Path(all_files[0]).stem
                scope = f"({filename})"
        
        action = "update" if status['modified'] else "add"
        
        return f"{commit_type}{scope}: {action} {stats['files']} file{'s' if stats['files'] > 1 else ''}"

class PreCommitHooks:
    """Pre-commit hook functionality."""
    
    @staticmethod
    def install_hooks():
        """Install pre-commit hooks."""
        hooks_dir = Path(".git/hooks")
        hooks_dir.mkdir(exist_ok=True)
        
        pre_commit_hook = hooks_dir / "pre-commit"
        hook_content = """#!/bin/sh
# Auto-generated pre-commit hook
echo "🔍 Running pre-commit checks..."

# Check for large files (>10MB)
large_files=$(git diff --cached --name-only | xargs -I {} find {} -size +10M 2>/dev/null)
if [ ! -z "$large_files" ]; then
    echo "❌ Large files detected (>10MB):"
    echo "$large_files"
    echo "Consider using Git LFS for large files."
    exit 1
fi

# Check for common secrets patterns
secrets=$(git diff --cached | grep -E "(password|secret|key|token).*=" | grep -v "# " || true)
if [ ! -z "$secrets" ]; then
    echo "⚠️ Potential secrets detected in staged changes:"
    echo "$secrets"
    echo "Please review before committing."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
"""
        
        with open(pre_commit_hook, 'w') as f:
            f.write(hook_content)
        
        # Make executable
        os.chmod(pre_commit_hook, 0o755)
        print("✅ Pre-commit hooks installed")

    @staticmethod
    def check_code_quality():
        """Run basic code quality checks."""
        python_files = GitOperations.run_command("git diff --cached --name-only --diff-filter=ACM | grep '\\.py$'")
        if python_files:
            print("🐍 Checking Python code quality...")
            for file in python_files.split('\n'):
                if file:
                    # Basic syntax check
                    result = subprocess.run([sys.executable, "-m", "py_compile", file], 
                                         capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"❌ Syntax error in {file}")
                        return False
        return True

def main():
    """Enhanced main function with argument parsing."""
    parser = argparse.ArgumentParser(description="AI-powered Git commit and push tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    parser.add_argument("--install-hooks", action="store_true", help="Install pre-commit hooks")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI message generation")
    parser.add_argument("--message", "-m", help="Use custom commit message")
    parser.add_argument("--model", default="mistral", help="Ollama model to use")
    
    args = parser.parse_args()
    
    try:
        # Install hooks if requested
        if args.install_hooks:
            PreCommitHooks.install_hooks()
            return
        
        # Update config
        config.ollama_model = args.model
        
        print("🚀 Enhanced Git Commit Push Assistant")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize Git repo if needed
        if not GitOperations.is_git_repo():
            if args.dry_run:
                print("DRY RUN: Would initialize Git repository")
            else:
                GitOperations.run_command("git init", capture_output=False)
                print("📁 Git repository initialized")
        
        # Get repository status
        status = GitOperations.get_repo_status()
        stats = GitOperations.get_file_changes()
        
        # Check if there are changes
        has_changes = any(files for files in status.values())
        if not has_changes:
            print("ℹ️ No changes detected in repository")
            print("✨ Repository is up to date!")
            return
        
        print(f"📊 Changes detected: {stats['files']} files, +{stats['additions']} -{stats['deletions']} lines")
        
        if args.dry_run:
            print("DRY RUN: Would stage and commit changes")
            print(f"Files to be added: {sum(len(files) for files in status.values())}")
            return
        
        # Run pre-commit checks
        if not PreCommitHooks.check_code_quality():
            print("❌ Code quality checks failed")
            return
        
        # Stage changes
        GitOperations.run_command("git add .", capture_output=False)
        print("📁 Changes staged")
        
        # Generate commit message
        commit_message = args.message
        if not commit_message and not args.no_ai:
            print("🤖 Generating AI commit message...")
            generator = CommitMessageGenerator(config.ollama_model)
            recent_commits = GitOperations.get_recent_commits()
            commit_message = generator.generate_enhanced_message(status, stats, recent_commits)
        
        # Fallback message
        if not commit_message:
            generator = CommitMessageGenerator()
            commit_message = generator.generate_fallback_message(status, stats)
            print(f"📝 Using fallback message: {commit_message}")
        else:
            print(f"✅ Commit message: {commit_message}")
        
        # Create commit
        GitOperations.run_command(f'git commit -m "{commit_message}"', capture_output=False)
        print(f"✅ Commit created: {commit_message}")
        
        # Configure branch and remote
        GitOperations.run_command(f"git branch -M {config.default_branch}", capture_output=False)
        
        existing_remote = GitOperations.run_command("git remote get-url origin")
        if not existing_remote:
            GitOperations.run_command(f"git remote add origin {config.remote_url}", capture_output=False)
            print(f"📡 Remote configured: {config.remote_url}")
        
        # Push to GitHub
        print("🚀 Pushing to GitHub...")
        push_result = GitOperations.run_command(f"git push -u origin {config.default_branch}", 
                                              capture_output=True, check=False)
        
        if push_result is not None:
            print("✅ Successfully pushed to GitHub!")
        else:
            print("⚠️ Push failed. Check SSH connection and repository permissions.")
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()