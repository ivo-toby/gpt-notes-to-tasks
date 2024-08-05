import os
import re
from utils.file_handler import load_notes, write_summary_to_file, create_output_dir


class LearningService:
    def __init__(self, learnings_file, learnings_output_dir):
        self.learnings_file = os.path.expanduser(learnings_file)
        self.learnings_output_dir = os.path.expanduser(learnings_output_dir)

    def load_learnings(self):
        return load_notes(self.learnings_file)

    def identify_new_learnings(self, content):
        pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\](.*?)(?=\n\[|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)
        new_learnings = []
        for timestamp, learning in matches:
            if "processed: true" not in learning:
                new_learnings.append((timestamp, learning.strip()))
        return new_learnings

    def add_metadata(self, learning_entry, filename):
        return f"{learning_entry}\n\nprocessed: true\nfilename: {filename}\n\n"

    def generate_markdown_file(self, timestamp, learning, title, tags):
        clean_title = re.sub(r"[^\w\s-]", "", title.lower())
        clean_title = re.sub(r"[-\s]+", "_", clean_title).strip("-_")
        filename = f"{clean_title}.md"

        content = f"# {title}\n\n"
        content += f"Date: {timestamp}\n\n"
        content += f"## Learning\n{learning}\n\n"
        content += f"## Tags\n{' '.join(tags)}\n\n"

        file_path = os.path.join(self.learnings_output_dir, filename)
        write_summary_to_file(file_path, content)
        return filename

    def process_new_learnings(self, openai_service):
        content = self.load_learnings()
        new_learnings = self.identify_new_learnings(content)

        print(f"Processing {len(new_learnings)} new learnings...")
        updated_content = content
        for timestamp, learning in new_learnings:
            print(f"Processing learning: {learning[:100]}...")
            title = openai_service.generate_learning_title(learning)
            print(f"Title: {title}")
            tags = openai_service.generate_learning_tags(learning)
            print(f"Tags: {tags}")

            os.makedirs(self.learnings_output_dir, exist_ok=True)

            filename = self.generate_markdown_file(timestamp, learning, title, tags)

            # Update the specific learning entry with metadata
            learning_entry = f"[{timestamp}]{learning}"
            updated_entry = self.add_metadata(learning_entry, filename)
            updated_content = updated_content.replace(learning_entry, updated_entry)

        write_summary_to_file(self.learnings_file, updated_content)
        print("Processing complete.")

