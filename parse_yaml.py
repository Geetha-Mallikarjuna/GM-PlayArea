import yaml
import os

with open('input.yaml', 'r') as f:
    data = yaml.safe_load(f)

require_files = data.get('require_files', [])

os.makedirs('changelogs', exist_ok=True)

with open('changelogs/packages-info.txt', 'w') as out:
    out.write('# 📦 Package Summary from input.yaml\n\n')
    # Write HTML table start tag
    out.write('<table border="1" cellpadding="5" cellspacing="0">\n')
    out.write('  <thead>\n')
    out.write('    <tr><th>Package</th><th>Version</th><th>Name</th></tr>\n')
    out.write('  </thead>\n')
    out.write('  <tbody>\n')
    for item in require_files:
        package = item.get('package', 'N/A')
        version = item.get('version', 'N/A')
        name = item.get('name', 'N/A')
        # Write each row as HTML
        out.write(f'    <tr><td>{package}</td><td>{version}</td><td>{name}</td></tr>\n')
    out.write('  </tbody>\n')
    out.write('</table>\n')
