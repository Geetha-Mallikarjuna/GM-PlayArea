"""
📘 Jira Changelog Processor

This script automates the generation of a structured HTML-formatted changelog summary
by extracting Jira issue IDs from changelog `.txt` or `.json` files, querying the Jira API
for detailed issue information, and writing a styled HTML table to a markdown file.

Key Features:
-------------
1. Parses changelog `.txt` and `.json` files to extract Jira IDs (e.g., ESS-1234, NMS-567).
2. Fetches each Jira issue's:
   - Title
   - Status
   - Pre-Change Notes (customfield_10131)
   - Post-Change Notes (customfield_10096)
   - 'Include in Release Notes' flag (customfield_10053)
3. Outputs a well-formatted HTML table embedded in a markdown file.

Use Case:
---------
Used in CI/CD workflows to generate automated release notes from commit messages 
and Jira metadata. Typically triggered by GitHub Actions or other automation systems.

Environment Variables Required:
-------------------------------
- `JIRA_URL`: Base URL of your Jira instance (e.g., https://yourcompany.atlassian.net)
- `JIRA_EMAIL`: Your Jira account email
- `JIRA_API_TOKEN`: API token with access to read Jira issues

Example:
--------
python3 jira_changelog_processor.py --changelogs ReleaseNotes/changelog.txt ReleaseNotes/notes.json --output ReleaseNotes/summary.md
"""

import os
import re
import sys
import json
import argparse
import requests


def extract_jira_ids_from_file(file_path):
    """
    Extract Jira IDs like ESS-1234, NMS-567, DOPS-7890 from a changelog file.

    Supports both .txt and .json formats.

    Args:
        file_path (str): Path to the changelog file.

    Returns:
        set: Set of Jira IDs found in the file.
    """
    pattern = re.compile(r'\b(?:ESS|NMS|DOPS)-\d{3,4}\b')
    ids = set()
    print(f"🔍 Processing file: {file_path}")

    try:
        if file_path.lower().endswith(".json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                text_content = json.dumps(data)  # Convert entire structure to string
                found = pattern.findall(text_content)
                if found:
                    print(f"📄 JSON match: {found}")
                    ids.update(found)

        elif file_path.lower().endswith(".txt"):
            with open(file_path, 'r') as f:
                for line in f:
                    found = pattern.findall(line)
                    if found:
                        print(f"📄 Text line match: {line.strip()} → {found}")
                        ids.update(found)
        else:
            print(f"⚠️ Unsupported file format: {file_path}")
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")

    return ids


def extract_text_from_adf(adf_json):
    """
    Recursively extracts plain text from Atlassian Document Format (ADF).

    Args:
        adf_json (dict or list): ADF structure.

    Returns:
        str: Flattened plain text.
    """
    if isinstance(adf_json, dict):
        if adf_json.get("type") == "text":
            return adf_json.get("text", "")
        elif "content" in adf_json:
            return ''.join(extract_text_from_adf(child) for child in adf_json["content"])
    elif isinstance(adf_json, list):
        return ''.join(extract_text_from_adf(item) for item in adf_json)
    return ''


def get_jira_details(jira_id):
    """
    Fetch summary, status, release notes, and inclusion flag from Jira.

    Args:
        jira_id (str): Jira issue key (e.g., DOPS-1234)

    Returns:
        dict: Dictionary with Jira issue info
    """
    base_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not base_url or not email or not token:
        raise EnvironmentError("❌ Missing JIRA_URL, JIRA_EMAIL, or JIRA_API_TOKEN in environment variables.")

    url = f"{base_url}/rest/api/3/issue/{jira_id}"
    print(f"🌐 Fetching from Jira: {jira_id}")

    headers = {"Accept": "application/json"}
    response = requests.get(url, auth=(email, token), headers=headers)

    if response.status_code != 200:
        print(f"⚠️ Failed to fetch {jira_id}: HTTP {response.status_code}")
        return {
            "jira": jira_id,
            "title": f"(Error {response.status_code})",
            "status": "—",
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
        "pre_change": extract_text_from_adf(fields.get(JIRA_FIELD_PRE_CHANGE, {})) or "—",
        "post_change": extract_text_from_adf(fields.get(JIRA_FIELD_POST_CHANGE, {})) or "—",
        "include_in_release_notes": fields.get(JIRA_FIELD_INCLUDE_FLAG, {}).get("value") if isinstance(fields.get(JIRA_FIELD_INCLUDE_FLAG), dict) else "—"
    }


def write_markdown_table(details_list, output_file):
    """
    Writes a markdown file containing an HTML-styled Jira summary table.

    Args:
        details_list (list): List of Jira info dictionaries.
        output_file (str): Output path for markdown file.
    """
    print(f"📝 Writing markdown to: {output_file}")
    with open(output_file, 'w') as f:
        f.write("<style>\n")
        f.write("table { width: 100%; border-collapse: collapse; table-layout: fixed; }\n")
        f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }\n")
        f.write("th:nth-child(1), td:nth-child(1) { width: 5%; white-space: nowrap; }\n")
        f.write("th:nth-child(2), td:nth-child(2) { width: 20%; white-space: wrap; }\n")
        f.write("th:nth-child(3), td:nth-child(3), th:nth-child(4), td:nth-child(4) { width: 5%; white-space: nowrap; }\n")
        f.write("th:nth-child(5), td:nth-child(5), th:nth-child(6), td:nth-child(6) { width: 10%; word-break: break-word; }\n")
        f.write("</style>\n")

        f.write("<table>\n")
        f.write("<tr><th>Jira ID</th><th>Title</th><th>Status</th><th>CustomerVisible</th><th>Pre-Change Note</th><th>Post-Change Note</th></tr>\n")

        for item in details_list:
            jira_link = f"<a href='{os.getenv('JIRA_URL')}/browse/{item['jira']}' target='_blank'>{item['jira']}</a>"
            f.write(
                f"<tr><td>{jira_link}</td><td>{item['title']}</td><td>{item['status']}</td>"
                f"<td>{item['include_in_release_notes']}</td><td>{item['pre_change']}</td><td>{item['post_change']}</td></tr>\n"
            )

        f.write("</table>\n")
    print("✅ Markdown table successfully written.")


def parse_changelog_files(changelog_files):
    """
    Collects all Jira IDs from multiple changelog files.

    Args:
        changelog_files (list): List of file paths (.txt or .json).

    Returns:
        set: Unique Jira IDs across all files.
    """
    all_ids = set()
    for file in changelog_files:
        if not os.path.exists(file):
            print(f"⚠️ Skipping missing file: {file}")
            continue
        all_ids.update(extract_jira_ids_from_file(file))
    return all_ids


def main():
    """
    Main entry point. Parses CLI args and processes changelog files.
    """
    parser = argparse.ArgumentParser(description="Generate Jira-based release notes table from changelog .txt or .json files.")
    parser.add_argument('--changelogs', nargs='+', required=True, help="Paths to changelog files (.txt or .json)")
    parser.add_argument('--output', required=True, help="Path to output .md file")

    args = parser.parse_args()

    jira_ids = parse_changelog_files(args.changelogs)
    if not jira_ids:
        print("⚠️ No Jira IDs found. Exiting.")
        sys.exit(0)

    jira_details = [get_jira_details(jira_id) for jira_id in sorted(jira_ids)]
    write_markdown_table(jira_details, args.output)


if __name__ == "__main__":
    main()
