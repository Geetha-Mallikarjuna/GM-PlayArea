import yaml
import os

# Load YAML
with open('input.yaml', 'r') as f:
    data = yaml.safe_load(f)

require_files = data.get('require_files', [])

# Ensure output directory
os.makedirs('changelogs', exist_ok=True)

# Write markdown table
with open('changelogs/packages-info.txt', 'w') as out:
    out.write('# 📦 Package Summary from input.yaml\n')
    out.write('| Package | Version | Name |\n')
    out.write('|---------|---------|------|\n')
    for item in require_files:
        package = item.get('package', 'N/A')
        version = item.get('version', 'N/A')
        name = item.get('name', 'N/A')
        out.write(f'| {package} | {version} | {name} |\n')
