import os
import re
from datetime import datetime
from utils.file_handler import load_notes, write_summary_to_file, create_output_dir


class LearningService:
    def __init__(self, learnings_file, learnings_output_dir):
        self.learnings_file = os.path.expanduser(learnings_file)
        self.learnings_output_dir = os.path.expanduser(learnings_output_dir)

    def load_learnings(self):
        return load_notes(self.learnings_file)

    def identify_new_learnings(self, content):
        pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] (.*?)(?=\n\[|$)"
        matches = re.findall(pattern, content, re.DOTALL)
        new_learnings = []
        for timestamp, learning in matches:
            if "processed: true" not in learning:
                new_learnings.append((timestamp, learning.strip()))
        return new_learnings

    def add_metadata(self, content, timestamp, filename):
        learning_pattern = re.escape(f"[{timestamp}]") + r"(.*?)(?=\n\[|$)"
        replacement = f"[{timestamp}]\\1\n\nprocessed: true\nfilename: {filename}\n"
        return re.sub(learning_pattern, replacement, content, flags=re.DOTALL)

    def generate_markdown_file(self, timestamp, learning, title, tags, related_links):
        # Clean the title for use as a filename
        clean_title = re.sub(r"[^\w\s-]", "", title.lower())
        clean_title = re.sub(r"[-\s]+", "_", clean_title).strip("-_")
        filename = f"{clean_title}.md"

        content = f"# {title}\n\n"
        content += f"Date: {timestamp}\n\n"
        content += f"## Learning\n{learning}\n\n"
        content += f"## Tags\n{', '.join(tags)}\n\n"
        if related_links:
            content += "## Related Learnings\n"
            for link in related_links:
                content += f"- [{link['title']}]({link['filename']})\n"

        file_path = os.path.join(self.learnings_output_dir, filename)
        write_summary_to_file(file_path, content)
        return filename

    def process_new_learnings(self, openai_service):
        content = self.load_learnings()
        new_learnings = self.identify_new_learnings(content)

        print(f"Processing {len(new_learnings)} new learnings...")
        for timestamp, learning in new_learnings:
            print(f"Processing learning: {learning[:100]}...")
            title = openai_service.generate_learning_title(learning)
            print(f"Title: {title}")
            tags = openai_service.generate_learning_tags(learning)
            print(f"Tags: {tags}")

            # Create the directory if it doesn't exist
            os.makedirs(self.learnings_output_dir, exist_ok=True)

            related_links = openai_service.identify_related_learnings(
                learning, self.learnings_output_dir
            )
            print(f"Related links: {related_links}")

            filename = self.generate_markdown_file(
                timestamp, learning, title, tags, related_links
            )
            content = self.add_metadata(content, timestamp, filename)

        write_summary_to_file(self.learnings_file, content)
        print("Processing complete.")

    def update_existing_learnings(self, openai_service):
        content = self.load_learnings()
        pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] (.*?)\n\nprocessed: true\nfilename: (.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)

        for timestamp, learning, filename in matches:
            file_path = os.path.join(self.learnings_output_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, "r") as file:
                    existing_content = file.read()

                title = re.search(r"# (.*?)\n", existing_content).group(1)
                tags = (
                    re.search(r"## Tags\n(.*?)\n", existing_content)
                    .group(1)
                    .split(", ")
                )

                related_links = openai_service.identify_related_learnings(
                    learning, self.learnings_output_dir
                )

                updated_content = self.generate_markdown_file(
                    timestamp, learning, title, tags, related_links
                )
                write_summary_to_file(file_path, updated_content)


create_output_dir(os.path.expanduser("~/Documents/learnings"))
