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
        pattern = r"(\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\](.*?)(?=\n\[|\Z))"
        matches = re.findall(pattern, content, re.DOTALL)
        return [
            (full_match.strip(), timestamp, learning.strip())
            for full_match, timestamp, learning in matches
        ]

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
        learnings = self.identify_new_learnings(content)

        print(f"Processing {len(learnings)} learnings...")
        for full_match, timestamp, learning in learnings:
            print(f"Processing learning: {learning[:100]}...")
            title = openai_service.generate_learning_title(learning)
            print(f"Title: {title}")
            tags = openai_service.generate_learning_tags(learning)
            print(f"Tags: {tags}")

            os.makedirs(self.learnings_output_dir, exist_ok=True)

            filename = self.generate_markdown_file(timestamp, learning, title, tags)

            # Remove the processed learning from the content
            content = content.replace(full_match, "").strip()

        # Remove any consecutive newlines
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Write the updated content back to the file
        write_summary_to_file(self.learnings_file, content)
        print(
            "Processing complete. Processed learnings have been removed from the source file."
        )
