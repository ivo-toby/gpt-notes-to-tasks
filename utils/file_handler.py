import os


def load_notes(filename):
    expanded_filename = os.path.expanduser(filename)
    with open(expanded_filename, "r") as file:
        return file.read()


def write_summary_to_file(filename, content):
    expanded_filename = os.path.expanduser(filename)
    with open(expanded_filename, "w") as file:
        file.write(content)


def create_output_dir(output_dir):
    expanded_dir = os.path.expanduser(output_dir)
    os.makedirs(expanded_dir, exist_ok=True)
    return expanded_dir

