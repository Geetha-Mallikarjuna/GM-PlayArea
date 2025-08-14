# .github/scripts/parse_yaml.py

import yaml
import os

with open('input.yaml', 'r') as f:
    data = yaml.safe_load(f)

require_files = data.get('require_files', [])

os.makedirs('changelogs', exist_ok=True)
with open('changelogs/packages-info.txt', 'w') as out:
    out.write('# 📦 Package Summary from input.yaml\n\n')
    for item in require_files:
        package = item.get('package', 'N/A')
        version = item.get('version', 'N/A')
        name = item.get('name', 'N/A')
        out.write(f'- **Package:** {package}, **Version:** {version}, **Name:** `{name}`\n')
