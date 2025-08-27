import argparse
import os
import re
import requests
import sys


def extract_jira_ids_from_file(file_path):
    """
    Extract Jira IDs like ESS-1234, NMS-567, DOPS-7890 from a changelog file.

    Args:
        file_path (str): Path to the changelog file.

    Returns:
        set: Set of Jira IDs found in the file.
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


def get_jira_details(jira_id):
    """
    Fetch summary, status, and release note fields from Jira.

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
    print(f"🌐 Requesting Jira title for {jira_id} from {url}")

    headers = { "Accept": "application/json" }
    response = requests.get(url, auth=(email, token), headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch {jira_id}: {response.status_code}")
        return {
            "jira": jira_id,
            "title": f"(Error {response.status_code})",
            "status": "—",
            "pre_change": "—",
            "post_change": "—"
        }

    issue = response.json()
    fields = issue.get("fields", {})

    # Change these to match your actual Jira custom field names
    JIRA_FIELD_PRE_CHANGE = "customfield_10131"
    JIRA_FIELD_POST_CHANGE = "customfield_10096"

    return {
        "jira": jira_id,
        "title": fields.get("summary", "—"),
        "status": fields.get("status", {}).get("name", "—"),
        "pre_change": extract_text_from_adf(fields.get(JIRA_FIELD_PRE_CHANGE, {})) or "—",
        "post_change": extract_text_from_adf(fields.get(JIRA_FIELD_POST_CHANGE, {})) or "—"
    }


def write_markdown_table(details_list, output_file):
    """
    Writes a markdown table of Jira issues to a file.

    Args:
        details_list (list): List of Jira info dictionaries.
        output_file (str): Path to write markdown file.
    """
    print(f"📝 Writing Jira summary table to: {output_file}")
    with open(output_file, 'w') as f:
        f.write("<style>\n")
        f.write("table { width: 100%; border-collapse: collapse; table-layout: fixed;  }\n")
        f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }\n")
        f.write("th:nth-child(1) { width: 10%; white-space: nowrap; }\n")
        f.write("th:nth-child(2) { width: 10%; }\n")
        f.write("th:nth-child(3) { width: 10%; }\n")
        f.write("th:nth-child(4), th:nth-child(5) { width: 25%; word-break: break-word; }\n")
        f.write("</style>\n")
        f.write("<table>\n")
        f.write("<tr><th>Jira ID</th><th>Title</th><th>Status</th><th>Pre-Change Note</th><th>Post-Change Note</th></tr>\n")

        for item in details_list:
            jira_link = f"<a href='{os.getenv('JIRA_URL')}/browse/{item['jira']}' target='_blank'>{item['jira']}</a>"
            f.write(f"<tr><td>{jira_link}</td><td>{item['title']}</td><td>{item['status']}</td>"
                    f"<td>{item['pre_change']}</td><td>{item['post_change']}</td></tr>\n")

        f.write("</table>\n")
    print("✅ Done writing Jira titles.")


def main():
    """
    Main entry point. Parses CLI args and processes Jira changelog files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--changelogs', nargs='+', required=True, help="Paths to changelog .txt files")
    parser.add_argument('--output', required=True, help="Path to output markdown file")
    args = parser.parse_args()

    print("📁 Changelog files to process:")
    for f in args.changelogs:
        print(f" - {f}")

    # Collect unique Jira IDs
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

    # Get full Jira info
    details_list = [get_jira_details(jira_id) for jira_id in sorted(jira_ids)]

    # Write markdown
    write_markdown_table(details_list, args.output)


if __name__ == "__main__":
    main()
