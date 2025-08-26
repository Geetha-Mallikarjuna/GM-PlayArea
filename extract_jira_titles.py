import os
import re
import requests

# Load credentials from environment
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

HEADERS = {
    "Accept": "application/json"
}

def extract_jira_ids(text):
    return sorted(set(re.findall(r'\b(ESS|NMS)-\d+\b', text)))

def fetch_jira_title(jira_id):
    url = f"{JIRA_URL}/rest/api/3/issue/{jira_id}"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    response = requests.get(url, headers=HEADERS, auth=auth)
    if response.status_code == 200:
        return response.json()['fields']['summary']
    return None

def process_changelog_file(input_file, output_file):
    with open(input_file, "r") as f:
        content = f.read()

    jira_ids = extract_jira_ids(content)

    with open(output_file, "w") as out:
        if not jira_ids:
            out.write("- No Jira issues found.\n")
            return
        for jid in jira_ids:
            title = fetch_jira_title(jid)
            if title:
                out.write(f"- {jid}: {title}\n")
            else:
                out.write(f"- {jid}: ⚠️ Could not fetch title\n")

def main():
    directory = "ReleaseNotes"
    for file in os.listdir(directory):
        if file.startswith("changelog-") and file.endswith(".txt"):
            input_path = os.path.join(directory, file)
            output_path = input_path.replace(".txt", ".md")
            process_changelog_file(input_path, output_path)

if __name__ == "__main__":
    main()
