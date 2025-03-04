import os

def dump_python_files(directory, output_file):
    # Delete the output file if it already exists
    if os.path.exists(output_file):
        os.remove(output_file)

    # Open the output file in write mode
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Walk through the directory
        for root, _, files in os.walk(directory):
            # Skip the 'venv' directory
            if 'venv' in root.split(os.sep):
                continue

            for file in files:
                if file.endswith('.py') and file != output_file:  # Ignore combined_files.txt
                    file_path = os.path.join(root, file)
                    # Write the file name as a header
                    outfile.write(f"# File: {file_path}\n\n")
                    # Read and write the content of the file
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write("\n\n")  # Add some space between files

# Specify the directory containing your Python files and the output file
project_directory = '.'  # Current directory (change as needed)
output_file = 'combined_files.txt'

# Combine the files
dump_python_files(project_directory, output_file)
print(f"All Python files have been combined into {output_file}")
