#!/usr/bin/env python3
"""
Add detailed technical comments to existing GitHub issues.

This script reads discovered bugs and adds comprehensive comments to matching
GitHub issues with:
- Detailed technical analysis
- Attack scenarios / reproduction steps
- Specific fix recommendations with code examples
- Cross-references to related issues

Usage:
    # Dry run (preview comments)
    python3 scripts/enhance_github_issues.py --dry-run --limit 2

    # Add comments to high priority issues only
    python3 scripts/enhance_github_issues.py --priority high --limit 10

    # Add comment to specific issue
    python3 scripts/enhance_github_issues.py --issue 14

    # Add comments to all matched issues
    python3 scripts/enhance_github_issues.py --all

Requirements:
    - gh CLI authenticated: gh auth login
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))
from issues_data import ISSUES


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    title = re.sub(r'^\[#\d+\]\s*', '', title)
    for prefix in ['Bug:', 'Feature:', 'Enhancement:', 'Critical:', 'Improvement:']:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
    return title.lower().strip()


def extract_issue_number(title: str) -> int:
    """Extract issue number from title like [#15]."""
    match = re.match(r'^\[#(\d+)\]', title)
    return int(match.group(1)) if match else None


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_github_issue_number(our_issue_idx: int, repo) -> int:
    """Find the GitHub issue number for our discovered issue."""
    # First try exact match from existing issues file
    existing_file = '/tmp/open_issues.txt'
    try:
        with open(existing_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '|' in line:
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        gh_number, title = parts
                        referenced_idx = extract_issue_number(title)
                        if referenced_idx == our_issue_idx:
                            return int(gh_number)
    except Exception:
        pass

    # Fall back to searching GitHub directly
    our_issue = ISSUES[our_issue_idx]
    our_normalized = normalize_title(our_issue['title'])

    issues = repo.get_issues(state='open')
    best_match = None
    best_score = 0

    for gh_issue in issues:
        gh_normalized = normalize_title(gh_issue.title)
        score = similarity(our_normalized, gh_normalized)
        if score > best_score:
            best_score = score
            best_match = gh_issue

    if best_score >= 0.75 and best_match:
        return best_match.number

    return None


def format_enhancement_comment(issue_idx: int) -> str:
    """Format a detailed enhancement comment for a GitHub issue."""
    issue = ISSUES[issue_idx]

    comment = f"## 🔍 Enhanced Technical Analysis\n\n"
    comment += f"This comment provides additional technical depth, attack scenarios, and fix recommendations.\n\n"
    comment += "---\n\n"

    # Issue details
    comment += f"### 📋 Issue Details\n\n"
    comment += f"**Original Index:** #{issue_idx}\n"
    comment += f"**Type:** `{issue['type']}`\n"
    comment += f"**Area:** `{issue['area']}`\n"
    comment += f"**Priority:** `{issue['priority']}`\n"
    comment += f"**Difficulty:** `{issue.get('level', 'level:intermediate')}`\n"

    if issue.get('gfi'):
        comment += f"**Good First Issue:** ✅ Yes - Great for new contributors!\n"

    comment += "\n"

    # Main description with enhanced formatting
    comment += f"### 📝 Detailed Description\n\n"
    body = issue['body']

    # Split body into sections if it contains "Fix:"
    if 'Fix:' in body or 'fix:' in body:
        parts = re.split(r'(Fix:|fix:)', body, maxsplit=1)
        description = parts[0].strip()
        fix_section = ''.join(parts[1:]).strip() if len(parts) > 1 else ""

        comment += f"{description}\n\n"

        if fix_section:
            comment += f"### 🔧 Recommended Fix\n\n"
            comment += f"{fix_section}\n\n"
    else:
        comment += f"{body}\n\n"

    # Add severity for security issues
    if 'security' in issue['type']:
        comment += f"### ⚠️ Security Impact\n\n"

        severity_keywords = {
            'CRITICAL': ['MITM', 'SSRF', 'cloud metadata', 'credential', 'RCE'],
            'HIGH': ['IDOR', 'bypass', 'injection', 'leak', 'exposure'],
            'MEDIUM': ['race condition', 'DoS', 'information disclosure']
        }

        severity = 'MEDIUM'
        for sev, keywords in severity_keywords.items():
            if any(keyword.lower() in issue['title'].lower() or keyword.lower() in body.lower()
                   for keyword in keywords):
                severity = sev
                break

        emoji = '🔴' if severity == 'CRITICAL' else '🟠' if severity == 'HIGH' else '🟡'
        comment += f"{emoji} **Severity:** {severity}\n\n"

        if severity == 'CRITICAL':
            comment += "**⚡ Immediate Action Required** - This vulnerability could lead to:\n"
            if 'MITM' in body or 'SSRF' in body:
                comment += "- Man-in-the-Middle attacks\n"
                comment += "- Server-Side Request Forgery to internal services\n"
                comment += "- Credential interception\n"
            if 'metadata' in body.lower():
                comment += "- Cloud provider credential theft (AWS/GCP/Azure)\n"
                comment += "- Instance role compromise\n"

        comment += "\n"

    # Add testing recommendations
    if 'test' not in issue['type']:
        comment += f"### 🧪 Testing Recommendations\n\n"

        if 'security' in issue['type']:
            comment += "**Security Tests:**\n"
            comment += "- [ ] Verify the vulnerability exists in current codebase\n"
            comment += "- [ ] Create proof-of-concept exploit\n"
            comment += "- [ ] Add security test that fails before fix\n"
            comment += "- [ ] Verify fix prevents exploitation\n"
            comment += "- [ ] Check for similar issues in related code\n\n"
        else:
            comment += "- [ ] Add unit test that reproduces the issue\n"
            comment += "- [ ] Verify test fails before fix\n"
            comment += "- [ ] Verify test passes after fix\n"
            comment += "- [ ] Add edge case tests\n\n"

    # Add related issues
    comment += f"### 🔗 Related Issues\n\n"
    comment += f"This issue is part of a comprehensive security audit. "
    comment += f"See the [complete report](https://github.com/utksh1/SecuScan/blob/main/DISCOVERED_BUGS_REPORT.md) for context.\n\n"

    # Find related issues by area or keywords
    related = []
    for idx, other in enumerate(ISSUES):
        if idx != issue_idx:
            # Same area and similar keywords
            if other['area'] == issue['area']:
                title_words = set(issue['title'].lower().split())
                other_words = set(other['title'].lower().split())
                if len(title_words & other_words) >= 2:
                    related.append(idx)

    if related:
        comment += "**Related issues from the same analysis:**\n"
        for rel_idx in related[:5]:  # Limit to 5
            comment += f"- Issue #{rel_idx}: {ISSUES[rel_idx]['title'][:60]}...\n"
        comment += "\n"

    # Footer
    comment += "---\n\n"
    comment += "*This enhanced analysis was generated from comprehensive security audit findings.*\n"
    comment += "*Analysis Date: July 9, 2026*\n"

    return comment


def add_comment_to_issue(repo, gh_issue_number: int, issue_idx: int, dry_run: bool = False):
    """Add enhancement comment to a GitHub issue."""
    comment_text = format_enhancement_comment(issue_idx)

    if dry_run:
        print("\n" + "="*80)
        print(f"WOULD ADD COMMENT TO ISSUE #{gh_issue_number} (Our Issue #{issue_idx})")
        print("="*80)
        print(comment_text)
        print("="*80)
        return True

    try:
        issue = repo.get_issue(gh_issue_number)

        # Check if we already commented
        for comment in issue.get_comments():
            if "Enhanced Technical Analysis" in comment.body:
                print(f"⚠️  Issue #{gh_issue_number} already has enhancement comment - skipping")
                return False

        issue.create_comment(comment_text)
        print(f"✓ Added enhancement comment to issue #{gh_issue_number} (Our #{issue_idx})")
        return True
    except Exception as e:
        print(f"✗ Failed to comment on issue #{gh_issue_number}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enhance existing GitHub issues with detailed analysis")
    parser.add_argument("--dry-run", action="store_true", help="Preview comments without posting")
    parser.add_argument("--issue", type=int, help="Enhance specific issue by index")
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Filter by priority")
    parser.add_argument("--type", choices=["bug", "security", "feature", "refactor", "performance"],
                        help="Filter by type")
    parser.add_argument("--area", choices=["backend", "frontend", "plugins"], help="Filter by area")
    parser.add_argument("--limit", type=int, help="Limit number of issues to enhance")
    parser.add_argument("--all", action="store_true", help="Enhance all matched issues (use with caution!)")
    parser.add_argument("--repo", default="utksh1/SecuScan", help="GitHub repo (owner/name)")
    parser.add_argument("--start-from", type=int, default=0, help="Start from issue index")

    args = parser.parse_args()

    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN")
    if not token and not args.dry_run:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("Export your token: export GITHUB_TOKEN='your_token'")
        sys.exit(1)

    # Initialize GitHub client
    if not args.dry_run:
        g = Github(token)
        try:
            repo = g.get_repo(args.repo)
            print(f"Connected to repository: {repo.full_name}")
        except Exception as e:
            print(f"ERROR: Failed to access repository {args.repo}: {e}")
            sys.exit(1)
    else:
        repo = None

    # Filter issues
    issues_to_enhance = []

    if args.issue is not None:
        if 0 <= args.issue < len(ISSUES):
            issues_to_enhance = [args.issue]
        else:
            print(f"ERROR: Issue index {args.issue} out of range (0-{len(ISSUES)-1})")
            sys.exit(1)
    else:
        # Apply filters
        for idx, issue in enumerate(ISSUES):
            if idx < args.start_from:
                continue

            if args.priority and args.priority not in issue['priority']:
                continue

            if args.type and args.type not in issue['type']:
                continue

            if args.area and args.area not in issue['area']:
                continue

            issues_to_enhance.append(idx)

        if args.limit:
            issues_to_enhance = issues_to_enhance[:args.limit]

    # Don't enhance all without explicit flag
    if len(issues_to_enhance) > 20 and not args.all and not args.dry_run:
        print(f"⚠️  WARNING: You're about to enhance {len(issues_to_enhance)} issues!")
        print("This will add comments to many GitHub issues.")
        print("Use --all flag to confirm, or --limit to reduce the count.")
        sys.exit(1)

    # Display summary
    print(f"\n{'DRY RUN - ' if args.dry_run else ''}Enhancing {len(issues_to_enhance)} issues...")

    if not args.dry_run and not args.issue:
        confirm = input(f"Add enhancement comments to {len(issues_to_enhance)} issues? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

    # Enhance issues
    enhanced = []
    skipped = []
    failed = []

    for idx, issue_idx in enumerate(issues_to_enhance):
        print(f"\n[{idx+1}/{len(issues_to_enhance)}] Processing issue #{issue_idx}...")

        # Find GitHub issue number
        if not args.dry_run:
            gh_number = find_github_issue_number(issue_idx, repo)
            if not gh_number:
                print(f"⚠️  Could not find GitHub issue for #{issue_idx} - skipping")
                skipped.append(issue_idx)
                continue
        else:
            gh_number = 1000 + issue_idx  # Fake number for dry run

        # Add comment
        success = add_comment_to_issue(repo, gh_number, issue_idx, args.dry_run)

        if success:
            enhanced.append((issue_idx, gh_number))
        else:
            failed.append(issue_idx)

    # Summary
    print(f"\n{'='*80}")
    if args.dry_run:
        print(f"DRY RUN: Would enhance {len(issues_to_enhance)} issues")
    else:
        print(f"✓ Enhanced {len(enhanced)} issues")
        if skipped:
            print(f"⚠️  Skipped {len(skipped)} issues (no match or already enhanced)")
        if failed:
            print(f"✗ Failed {len(failed)} issues")

        if enhanced:
            print(f"\nEnhanced issues:")
            for our_idx, gh_num in enhanced[:10]:
                print(f"  - Issue #{our_idx} → GitHub #{gh_num}")
            if len(enhanced) > 10:
                print(f"  ... and {len(enhanced) - 10} more")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
