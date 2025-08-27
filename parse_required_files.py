"""
Package Summary Generator

This script parses a YAML file containing package requirements and generates
an HTML-formatted package summary as a table saved to a specified output file.

It is hardcoded to use:
  Input:  'CI_create_package/required_files.yaml'
  Output: 'ReleaseNotes/packages-info.txt'

Features:
- Loads and parses YAML content safely.
- Generates an HTML table summarizing package, version, and name fields.
- Ensures output directory exists before writing.
- Modular design to allow reuse in other projects or workflows.

"""

import yaml
import os
import logging
from typing import List, Dict, Optional

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_yaml(file_path: str) -> Optional[Dict]:
    """
    Loads a YAML file and returns the parsed data.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict or None: Parsed YAML content if successful, None otherwise.
    """
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"YAML file not found: {file_path}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {file_path}: {e}")
    return None

def ensure_directory(directory: str) -> None:
    """
    Ensures the specified directory exists, creates it if not.

    Args:
        directory (str): Directory path to create.
    """
    os.makedirs(directory, exist_ok=True)
    logging.debug(f"Ensured directory exists: {directory}")

def generate_html_table(require_files: List[Dict]) -> str:
    """
    Generates an HTML table string summarizing package info.

    Args:
        require_files (List[Dict]): List of dictionaries containing package info.

    Returns:
        str: HTML string representing the package summary table.
    """
    rows = []
    for item in require_files:
        package = item.get('package', 'N/A')
        version = item.get('version', 'N/A')
        name = item.get('name', 'N/A')
        rows.append(f'    <tr><td>{package}</td><td>{version}</td><td>{name}</td></tr>')

    html_table = (
        '<table border="1" cellpadding="5" cellspacing="0">\n'
        '  <thead>\n'
        '    <tr><th>Package</th><th>Version</th><th>Name</th></tr>\n'
        '  </thead>\n'
        '  <tbody>\n'
        f"{os.linesep.join(rows)}\n"
        '  </tbody>\n'
        '</table>\n'
    )
    return html_table

def write_package_summary(require_files: List[Dict], output_path: str) -> None:
    """
    Writes the package summary as an HTML table to the output file.

    Args:
        require_files (List[Dict]): List of package info dictionaries.
        output_path (str): File path to write the summary.
    """
    directory = os.path.dirname(output_path)
    if directory:
        ensure_directory(directory)

    html_content = generate_html_table(require_files)
    with open(output_path, 'w') as out_file:
        out_file.write(html_content)
    logging.info(f"Package summary successfully written to '{output_path}'")

def main() -> None:
    """
    Main function to load hardcoded YAML input and write the summary to hardcoded output.
    """
    input_file = 'CI_create_package/required_files.yaml'
    output_file = 'ReleaseNotes/packages-info.txt'

    logging.info(f"Loading YAML data from '{input_file}'...")
    data = load_yaml(input_file)
    if data is None:
        logging.error("Failed to load YAML data. Exiting.")
        return

    require_files = data.get('require_files', [])
    if not require_files:
        logging.warning(f"No 'require_files' section found or it's empty in '{input_file}'. Nothing to write.")
        return

    logging.info(f"Generating package summary to '{output_file}'...")
    write_package_summary(require_files, output_file)
    logging.info("✅ Package summary creation completed.")

if __name__ == "__main__":
    setup_logging()
    main()
