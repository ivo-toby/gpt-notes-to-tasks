import os


def load_notes(filename):
    with open(filename, "r") as file:
        return file.read()


def write_summary_to_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)


def create_output_dir(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
