"""
GitHub Repository Monitor Script
--------------------------------

Description:
    This script checks a specified GitHub organization (or user) for:
    - New repositories added since the last check.
    - Changes in archived status of existing repositories.

    It compares the current repository state with a previously saved state
    (`repos_state.json`). On first run, it initializes the state without
    reporting changes.

How it works:
    - Uses GitHub API (requires a GitHub token).
    - Fetches all repositories for the given org/user (supports pagination).
    - Saves the current state (repo names and their archived status).
    - Compares against the last saved state to detect changes.

Environment Variables Required:
    GITHUB_TOKEN : GitHub personal access token (with `repo` or `public_repo` scope).
    GITHUB_ORG   : GitHub organization or username to monitor.

Output:
    - Prints new repositories.
    - Prints repositories with changed archived status.
    - Skips comparison on first run.

Usage:
    $ export GITHUB_TOKEN=your_token
    $ export GITHUB_ORG=your_org
    $ python check_repos.py

Author:
    ChatGPT / OpenAI (customized per user request)
"""

import os
import json
import requests
from typing import Dict, List, Tuple

# Constants for env vars and state file
GITHUB_TOKEN_ENV = "GITHUB_TOKEN"
GITHUB_ORG_ENV = "GITHUB_ORG"
STATE_FILE = "repos_state.json"

def fetch_all_repos(org: str, token: str) -> List[Dict]:
    """
    Fetch all repositories for the given GitHub organization/user using the GitHub API.
    Supports pagination for large orgs.
    """
    repos = []
    page = 1
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    while True:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

        data = response.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos

def load_previous_state(filename: str) -> Tuple[Dict[str, bool], bool]:
    """
    Load previous state from a JSON file. If it doesn't exist, return empty dict and is_first_run=True.
    """
    if not os.path.exists(filename):
        return {}, True
    with open(filename, "r") as f:
        return json.load(f), False

def save_current_state(state: Dict[str, bool], filename: str) -> None:
    """
    Save current repository state to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(state, f, indent=2)

def analyze_repo_changes(
    old_state: Dict[str, bool], 
    new_state: Dict[str, bool]
) -> Tuple[List[str], List[str]]:
    """
    Compare old and new repo states to detect new repositories and changes in archived status.
    """
    new_repos = [repo for repo in new_state if repo not in old_state]
    archived_changed = [
        repo for repo in new_state
        if repo in old_state and new_state[repo] != old_state[repo]
    ]
    return new_repos, archived_changed

def print_changes(
    new_repos: List[str], 
    archived_changed: List[str], 
    old_state: Dict[str, bool], 
    new_state: Dict[str, bool]
) -> None:
    """
    Print newly added repositories and those with changed archived status.
    """
    if new_repos:
        print("🆕 New repositories added:")
        for repo in new_repos:
            print(f"- {repo} (archived={new_state[repo]})")
    else:
        print("✅ No new repositories added.")

    if archived_changed:
        print("\n🔄 Repositories with changed archived status:")
        for repo in archived_changed:
            print(f"- {repo}: archived status changed from {old_state[repo]} to {new_state[repo]}")
    else:
        print("✅ No repositories changed archived status.")

def main():
    # Load environment variables
    github_token = os.getenv(GITHUB_TOKEN_ENV)
    github_org = os.getenv(GITHUB_ORG_ENV)

    if not github_token or not github_org:
        print(f"❌ ERROR: Missing environment variables {GITHUB_TOKEN_ENV} and/or {GITHUB_ORG_ENV}.")
        exit(1)

    # Fetch current repositories
    repos = fetch_all_repos(github_org, github_token)
    current_state = {repo['name']: repo['archived'] for repo in repos}

    # Load previous state
    old_state, is_first_run = load_previous_state(STATE_FILE)

    if is_first_run:
        print("🚀 First run detected. Saving current state and skipping comparison.")
    else:
        # Compare and print changes
        new_repos, archived_changed = analyze_repo_changes(old_state, current_state)
        print_changes(new_repos, archived_changed, old_state, current_state)

    # Save current state for future comparison
    save_current_state(current_state, STATE_FILE)

if __name__ == "__main__":
    main()
