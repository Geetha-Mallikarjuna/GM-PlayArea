import yaml
import os

def load_yaml(file_path):
    """
    Loads a YAML file and returns the parsed data.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Parsed YAML content.
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def create_ReleaseNotes_directory(directory='ReleaseNotes'):
    """
    Ensures the ReleaseNotes directory exists.

    Args:
        directory (str): Directory name to create.
    """
    os.makedirs(directory, exist_ok=True)

def write_package_summary(require_files, output_path):
    """
    Writes the package summary into a Markdown table inside a text file.

    This format is compatible with Pandoc for later conversion to HTML.

    Args:
        require_files (list): List of dicts with package info.
        output_path (str): File path to write the summary to.
    """
    with open(output_path, 'w') as out:
        # Write Markdown table header (3 columns)
        out.write("| Package | Version | Name |\n")
        out.write("|---------|---------|------|\n")

        # Loop through each required package and write as a Markdown row
        for item in require_files:
            package = item.get('package', 'N/A')
            version = item.get('version', 'N/A')
            name = item.get('name', 'N/A')
            out.write(f"| {package} | {version} | {name} |\n")

def main():
    """
    Main function to parse required_files.yaml and generate package summary.
    """
    input_file = 'CI_create_package/required_files.yaml'
    output_file = 'ReleaseNotes/packages-info.txt'

    # Load YAML data
    print(f"📥 Loading YAML data from '{input_file}'...")
    data = load_yaml(input_file)

    # Extract required files section
    require_files = data.get('require_files', [])

    # Prepare output directory
    print("📂 Ensuring 'ReleaseNotes' directory exists...")
    create_ReleaseNotes_directory()

    # Generate the Markdown summary
    print(f"📝 Writing package summary to '{output_file}'...")
    write_package_summary(require_files, output_file)

    print("✅ Done! Package summary created.")

if __name__ == "__main__":
    main()
