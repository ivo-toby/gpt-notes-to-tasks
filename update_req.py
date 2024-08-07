import os
import subprocess


def update_requirements():
    # Install pipreqs if not already installed
    subprocess.run(["pip", "install", "pipreqs"], check=True)

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Run pipreqs
    subprocess.run(["pipreqs", current_dir, "--force"], check=True)

    print("requirements.txt has been updated.")


if __name__ == "__main__":
    update_requirements()
