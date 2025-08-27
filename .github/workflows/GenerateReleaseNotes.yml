import argparse
import os
import re
import requests
import sys

# -------------------------------
# Configuration for custom fields
# -------------------------------

# Update these based on your Jira setup (use actual field IDs!)
JIRA_FIELD_PRE_CHANGE = "customfield_10131"   # Replace with actual field ID
JIRA_FIELD_POST_CHANGE = "customfield_10096"  # Replace with actual field ID

# -------------------------------
# Helper Function: Extract Jira IDs from a file
# -------------------------------

def extract_jira_ids_from_file(file_path):
    """
    Scans a file line by line and extracts all Jira IDs matching
    the pattern DOPS-123, ESS-456, or NMS-789.

    Args:
        file_path (str): Path to the changelog file.

    Returns:
        set: Unique set of matched Jira IDs.
    """
    pattern = re.compile(r'\b(?:ESS|NMS|DOPS)-\d{3,4}\b')
    ids = set()

    print(f"🔍 Reading changelog: {file_path}")
    with open(file_path, 'r') as f:
        for line in f:
            found = pattern.findall(line)
            if found:
                print(f"✅ Found Jira IDs: {found}")
            ids.update(found)

    return ids

# -------------------------------
# Helper Function: Get Jira Issue Details
# -------------------------------

def get_jira_details(jira_id):
    """
    Fetches summary, status, and custom release note fields from a Jira issue.

    Args:
        jira_id (str): The Jira issue key (e.g., DOPS-123).

    Returns:
        dict: Issue details (id, title, status, pre/post change notes).
    """
    base_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([base_url, email, token]):
        raise EnvironmentError("❌ Missing Jira credentials in environment variables.")

    url = f"{base_url}/rest/api/3/issue/{jira_id}"
    headers = {"Accept": "application/json"}

    print(f"🌐 Fetching Jira issue: {jira_id}")
    response = requests.get(url, auth=(email, token), headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch {jira_id} (Status: {response.status_code})")
        return {
            "id": jira_id,
            "title": f"(Error {response.status_code})",
            "status": "Unknown",
            "pre_change": "—",
            "post_change": "—"
        }

    data = response.json()
    fields = data.get("fields", {})

    # Extract values with safe fallback
    title = fields.get("summary", "No Title")
    status = fields.get("status", {}).get("name", "Unknown")
    pre_change = fields.get(JIRA_FIELD_PRE_CHANGE, "").strip() or "—"
    post_change = fields.get(JIRA_FIELD_POST_CHANGE, "").strip() or "—"

    return {
        "id": jira_id,
        "title": title,
        "status": status,
        "pre_change": pre_change,
        "post_change": post_change
    }

# -------------------------------
# Function: Process changelog files
# -------------------------------

def collect_all_jira_ids(changelog_files):
    """
    Iterates over multiple changelog files and collects all Jira IDs.

    Args:
        changelog_files (list): List of file paths.

    Returns:
        set: Combined set of all Jira IDs found.
    """
    all_ids = set()
    for file in changelog_files:
        if not os.path.exists(file):
            print(f"⚠️ Skipping missing file: {file}")
            continue
        all_ids.update(extract_jira_ids_from_file(file))
    return all_ids

# -------------------------------
# Function: Write output to Markdown table
# -------------------------------

def write_output_table(jira_details_list, output_path):
    """
    Writes a Markdown table with Jira details.

    Args:
        jira_details_list (list of dict): List of issue details.
        output_path (str): Output file path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        if not jira_details_list:
            f.write("_No Jira issues found._\n")
            print(f"⚠️ No Jira IDs found. Output written to {output_path}")
            return

        f.write("| Jira ID | Title | Status | Release Notes - Pre Change | Release Notes - Post Change |\n")
        f.write("|---------|--------|-------|-----------------------------|------------------------------|\n")

        for issue in jira_details_list:
            f.write(f"| {issue['id']} | {issue['title']} | {issue['status']} | {issue['pre_change']} | {issue['post_change']} |\n")

    print(f"✅ Jira report written to: {output_path}")

# -------------------------------
# Main Entry Point
# -------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract Jira details from changelogs.")
    parser.add_argument('--changelogs', nargs='+', required=True, help='Paths to changelog files.')
    parser.add_argument('--output', required=True, help='Markdown output file path.')
    args = parser.parse_args()

    print("📁 Processing changelog files...")
    jira_ids = collect_all_jira_ids(args.changelogs)

    print(f"📌 Total Jira IDs found: {len(jira_ids)}")

    details_list = [get_jira_details(jira_id) for jira_id in sorted(jira_ids)]
    write_output_table(details_list, args.output)

# -------------------------------
# Script Execution
# -------------------------------

if __name__ == "__main__":
    main()
