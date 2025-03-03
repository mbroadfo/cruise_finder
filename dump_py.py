import os

def dump_python_files(directory, output_file):
    # Open the output file in write mode
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Walk through the directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):  # Only process Python files
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