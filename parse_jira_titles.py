import argparse
import os
import re
import requests
import sys

def extract_jira_ids_from_file(file_path):
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

def get_jira_title(jira_id):
    base_url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not base_url or not email or not token:
        raise ValueError("❌ Missing one of: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN")

    url = f"{base_url}/rest/api/3/issue/{jira_id}"
    print(f"🌐 Requesting Jira title for {jira_id} from {url}")
    headers = { "Accept": "application/json" }

    response = requests.get(url, auth=(email, token), headers=headers)

    if response.status_code == 200:
        title = response.json()["fields"]["summary"]
        print(f"✅ {jira_id} → {title}")
        return title
    else:
        print(f"❌ Failed to fetch {jira_id}: {response.status_code}")
        return f"(Error {response.status_code})"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--changelogs', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    print("📁 Changelog files to process:")
    for f in args.changelogs:
        print(f" - {f}")

    jira_ids = set()
    for file in args.changelogs:
        if not os.path.exists(file):
            print(f"⚠️ Skipping missing file: {file}")
            continue
        jira_ids.update(extract_jira_ids_from_file(file))

    if not jira_ids:
        print("⚠️ No Jira IDs found across changelogs. Exiting.")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    print(f"📝 Writing Jira summary to: {args.output}")

    with open(args.output, 'w') as f:
        for jira_id in sorted(jira_ids):
            title = get_jira_title(jira_id)
            f.write(f"- {jira_id}: {title}\n")

    print("✅ Done writing Jira titles.")

if __name__ == "__main__":
    main()
