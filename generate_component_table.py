# scripts/generate_component_table.py

import yaml
import sys

def generate_table(yaml_path: str) -> str:
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    html = ["<h2 style='margin-top:30px;'>Component Versions</h2>"]
    html.append("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>")
    html.append("<tr><th>Component</th><th>Version</th></tr>")

    for key, value in sorted(data.items()):
        component = key.replace("nms_", "").replace("_version", "").replace("_", " ").title()
        html.append(f"<tr><td>{component}</td><td>{value}</td></tr>")

    html.append("</table>")
    return "\n".join(html)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_component_table.py <yaml_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    html_output = generate_table(yaml_file)
    print(html_output)
