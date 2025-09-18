"""
📘 Jira Changelog Processor with Delivery & Conditional Status Updates

This script automates:
1. Generating a structured HTML-formatted changelog summary.
2. Updating Jira issues with delivery details (e.g., version field).
3. Transitioning Jira issues to "Ready for Verification" **only if the issue type is Bug**.

Key Features:
-------------
1. Parses changelog `.txt` files to extract Jira IDs (e.g., ESS-1234, NMS-567).
2. Fetches each Jira issue's:
   - Title
   - Status
   - Type (e.g., Bug, Task, Story)
   - Pre-Change Notes (customfield_10131)
   - Post-Change Notes (customfield_10096)
   - 'Include in Release Notes' flag (customfield_10053)
3. Updates Jira issues to include:
   - Delivery version (via `fixVersions` field).
   - Status → "Ready for Verification" (only if issue type = Bug).
4. Outputs a well-formatted HTML table embedded in a markdown file.

Use Case:
---------
- CI/CD workflows to generate automated release notes from commit messages
  and Jira metadata.
- Ensures delivery versions are tagged in Jira.
- Transitions Bugs to verification stage after release packaging.

Environment Variables Required:
-------------------------------
- `JIRA_URL`: Base URL of your Jira instance (e.g., https://yourcompany.atlassian.net)
- `JIRA_EMAIL`: Your Jira account email
- `JIRA_API_TOKEN`: API token with access to read/write Jira issues

Example:
--------
python3 parse_jira_titles.py \
    --changelogs ReleaseNotes/changelog-*.txt \
    --output ReleaseNotes/markdone.md \
    --version 1.2.3
"""

import argparse
import os
import re
import requests
import sys


# ------------------------------------------------------------------------------
# 📌 Utility: Extract Jira IDs from changelog
# ------------------------------------------------------------------------------
def extract_jira_ids_from_file(file_path):
    """
    Extract Jira IDs like ESS-1234, NMS-567, DOPS-7890 from a changelog file.

    Args:
        file_path (str): Path to the changelog file.

    Returns:
        set: Unique Jira IDs found in the file.
    """
    pattern = re.compile(r'\b(?:ESS|NMS|DOPS)-\d{3,4}\b')
    ids = set()
    print(f"🔍 Reading changelog: {file_path}")
    with open(file_path, 'r') as f:
        for line in f:
            found = pattern.findall(line)
            if found:
                print(f"✅ Found Jira IDs in line: {line.strip()} → {found}")
            ids.update(found)
    return ids


# ------------------------------------------------------------------------------
# 📌 Utility: Extract plain text from Atlassian Document Format (ADF)
# ------------------------------------------------------------------------------
def extract_text_from_adf(adf_json):
    """
    Recursively extracts plain text from Atlassian Document Format (ADF).

    Args:
        adf_json (dict or list): ADF structure.

    Returns:
        str: Flattened text content.
    """
    if isinstance(adf_json, dict):
        if adf_json.get("type") == "text":
            return adf_json.get("text", "")
        elif "content" in adf_json:
            return ''.join(extract_text_from_adf(child) for child in adf_json["content"])
    elif isinstance(adf_json, list):
        return ''.join(extract_text_from_adf(item) for item in adf_json)
    return ''


# ------------------------------------------------------------------------------
# 📌 Jira: Fetch issue details
# ------------------------------------------------------------------------------
def get_jira_details(jira_id):
    """
    Fetch summary, status, type, release notes, and inclusion flag from Jira.

    Args:
        jira_id (str): Jira issue key (e.g., DOPS-1234)

    Returns:
        dict: Dictionary with Jira issue info
    """
    base_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not base_url or not email or not token:
        raise ValueError("❌ Missing JIRA_URL, JIRA_EMAIL, or JIRA_API_TOKEN in environment variables.")

    url = f"{base_url}/rest/api/3/issue/{jira_id}"
    print(f"🌐 Requesting Jira details for {jira_id}")

    headers = {"Accept": "application/json"}
    response = requests.get(url, auth=(email, token), headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch {jira_id}: {response.status_code}")
        return {
            "jira": jira_id,
            "title": f"(Error {response.status_code})",
            "status": "—",
            "type": "—",
            "pre_change": "—",
            "post_change": "—",
            "include_in_release_notes": "—"
        }

    issue = response.json()
    fields = issue.get("fields", {})

    # Custom field IDs
    JIRA_FIELD_PRE_CHANGE = "customfield_10131"
    JIRA_FIELD_POST_CHANGE = "customfield_10096"
    JIRA_FIELD_INCLUDE_FLAG = "customfield_10053"

    return {
        "jira": jira_id,
        "title": fields.get("summary", "—"),
        "status": fields.get("status", {}).get("name", "—"),
        "type": fields.get("issuetype", {}).get("name", "—"),
        "pre_change": extract_text_from_adf(fields.get(JIRA_FIELD_PRE_CHANGE, {})) or "—",
        "post_change": extract_text_from_adf(fields.get(JIRA_FIELD_POST_CHANGE, {})) or "—",
        "include_in_release_notes": fields.get(JIRA_FIELD_INCLUDE_FLAG, {}).get("value")
        if isinstance(fields.get(JIRA_FIELD_INCLUDE_FLAG), dict) else "—"
    }


# ------------------------------------------------------------------------------
# 📌 Jira: Update delivery version & conditional transition
# ------------------------------------------------------------------------------
def update_jira_delivery_and_status(jira_id, version, issue_type):
    """
    Updates delivery details (fixVersions) and transitions issue to 'Ready for Verification'
    only if issue type is Bug.

    Args:
        jira_id (str): Jira issue key
        version (str): Version string to set in fixVersions
        issue_type (str): Type of the Jira issue (e.g., Bug, Task, Story)
    """
    base_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not base_url or not email or not token:
        raise ValueError("❌ Missing JIRA_URL, JIRA_EMAIL, or JIRA_API_TOKEN in environment variables.")

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # 1️⃣ Always update delivery details (fixVersions field)
    update_url = f"{base_url}/rest/api/3/issue/{jira_id}"
    payload = {
    "fields": {
        "customfield_10097": version
     }
    }
    print(f"🚚 Updating delivery details for {jira_id} → version {version}")
    response = requests.put(update_url, auth=(email, token), headers=headers, json=payload)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Failed to update fixVersion for {jira_id}: {response.status_code} {response.text}")

    # 2️⃣ Transition status → "Ready for Verification" (only if Bug)
    if issue_type.lower() != "bug":
        print(f"ℹ️ Skipping transition for {jira_id} (type: {issue_type})")
        return

    transitions_url = f"{base_url}/rest/api/3/issue/{jira_id}/transitions"
    transitions_resp = requests.get(transitions_url, auth=(email, token), headers=headers)
    if transitions_resp.status_code != 200:
        print(f"⚠️ Could not fetch transitions for {jira_id}: {transitions_resp.status_code}")
        return

    transitions = transitions_resp.json().get("transitions", [])
    target_transition = next((t for t in transitions if t["name"].lower() == "ready for verification"), None)

    if not target_transition:
        print(f"⚠️ No transition found for 'Ready for Verification' on {jira_id}")
        return

    transition_id = target_transition["id"]
    print(f"🔄 Transitioning {jira_id} → 'Ready for Verification'")
    transition_payload = {"transition": {"id": transition_id}}
    transition_resp = requests.post(transitions_url, auth=(email, token), headers=headers, json=transition_payload)

    if transition_resp.status_code not in [200, 204]:
        print(f"⚠️ Failed to transition {jira_id}: {transition_resp.status_code} {transition_resp.text}")


# ------------------------------------------------------------------------------
# 📌 Output: Write results to markdown
# ------------------------------------------------------------------------------
def write_markdown_table(details_list, output_file):
    """
    Writes a styled HTML table of Jira issues to a markdown file.

    Args:
        details_list (list): List of Jira info dictionaries.
        output_file (str): Path to write markdown file.
    """
    print(f"📝 Writing Jira summary table to: {output_file}")
    with open(output_file, 'w') as f:
        f.write("<style>\n")
        f.write("table { width: 100%; border-collapse: collapse; table-layout: fixed; }\n")
        f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }\n")
        f.write("th:nth-child(1), td:nth-child(1) { width: 5%; white-space: nowrap; }\n")
        f.write("th:nth-child(2), td:nth-child(2) { width: 10%; white-space: nowrap; }\n")
        f.write("th:nth-child(3), td:nth-child(3), th:nth-child(4), td:nth-child(4) { width: 5%; white-space: nowrap; }\n")
        f.write("th:nth-child(5), td:nth-child(5), th:nth-child(6), td:nth-child(6) { width: 20%; word-break: break-word; }\n")
        f.write("</style>\n")

        f.write("<table>\n")
        f.write("<tr><th>Jira ID</th><th>Title</th><th>Status</th><th>Type</th><th>CustomerVisible</th>"
                "<th>Pre-Change Note</th><th>Post-Change Note</th></tr>\n")

        for item in details_list:
            jira_link = f"<a href='{os.getenv('JIRA_URL')}/browse/{item['jira']}' target='_blank'>{item['jira']}</a>"
            f.write(
                f"<tr><td>{jira_link}</td><td>{item['title']}</td><td>{item['status']}</td><td>{item['type']}</td>"
                f"<td>{item['include_in_release_notes']}</td><td>{item['pre_change']}</td><td>{item['post_change']}</td></tr>\n"
            )

        f.write("</table>\n")
    print("✅ Done writing Jira summary.")


# ------------------------------------------------------------------------------
# 📌 Main Entry Point
# ------------------------------------------------------------------------------
def main():
    """
    Main entry point. Parses CLI args, processes Jira changelog files,
    generates summary, updates delivery info, and transitions Jira status.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--changelogs', nargs='+', required=True, help="Paths to changelog .txt files")
    parser.add_argument('--output', required=True, help="Path to output markdown file")
    parser.add_argument('--version', required=True, help="Version string to update in Jira (e.g., 1.2.3)")
    args = parser.parse_args()

    print("📁 Changelog files to process:")
    for f in args.changelogs:
        print(f" - {f}")

    # Step 1️⃣ Extract Jira IDs
    jira_ids = set()
    for file in args.changelogs:
        if not os.path.exists(file):
            print(f"⚠️ Skipping missing file: {file}")
            continue
        jira_ids.update(extract_jira_ids_from_file(file))

    if not jira_ids:
        print("⚠️ No Jira IDs found. Writing default message.")
        with open(args.output, 'w') as f:
            f.write("_No Jira issues found in changelogs._\n")
        sys.exit(0)

    # Step 2️⃣ Fetch Jira details & update delivery + status
    details_list = []
    for jira_id in sorted(jira_ids):
        details = get_jira_details(jira_id)
        details_list.append(details)

        # Update each Jira with version + conditional transition
        update_jira_delivery_and_status(jira_id, args.version, details["type"])

    # Step 3️⃣ Write final report
    write_markdown_table(details_list, args.output)


if __name__ == "__main__":
    main()
