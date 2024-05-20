from datetime import datetime, timedelta
import os
import applescript
import re
import yaml
import argparse
from openai import OpenAI

# Retrieve OpenAI API key from environment variable


def load_config(config_file):
    with open(config_file, "r") as file:
        return yaml.safe_load(file)


# Function to load notes from the Markdown file
def load_notes(filename):
    with open(filename, "r") as file:
        return file.read()


# Function to extract notes for the current day
def extract_today_notes(notes):
    today_str = datetime.now().strftime("%Y-%m-%d")
    pattern = re.compile(
        rf"\[{today_str}.*?\].*?(?=\[\d{{4}}-\d{{2}}-\d{{2}}|\Z)", re.DOTALL
    )
    today_notes = pattern.findall(notes)
    return "\n".join(today_notes)


# Function to summarize notes and identify action items using GPT-4o
def summarize_notes_and_identify_tasks(client, model, notes):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"Summarize the following notes, list actionable items, and add relevant tags to the end of the summary, tags should be written snake-case style:\n{notes}",
            },
        ],
        functions=[
            {
                "name": "summarize_notes_and_tasks",
                "description": "Summarize notes and list actionable items",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "tasks": {"type": "array", "items": {"type": "string"}},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "tasks", "tags"],
                },
            }
        ],
        function_call={"name": "summarize_notes_and_tasks"},
    )
    arguments = response.choices[0].message.function_call.arguments
    return eval(
        arguments
    )  # Converting string representation of dictionary to dictionary


# Function to add tasks to Apple Reminders
def add_to_reminders(task):
    script = f"""
    tell application "Reminders"
        set myRemind to (current date) + 1 * days
        set the time of myRemind to 9 * hours
        make new reminder with properties {{name:"{task}", due date:myRemind}}
    end tell
    """
    applescript.run(script)


# Function to write summary and tasks to a Markdown file
def write_summary_to_file(summary, tasks, tags, filename):
    with open(filename, "w") as file:
        file.write("# Daily Summary\n\n")
        file.write(f"## Summary\n\n{summary}\n\n")
        file.write(f"### Tags\n\n{' '.join([f'#{tag}' for tag in tags])}\n\n")
        file.write("## Action Items\n\n")
        for task in tasks:
            file.write(f"- {task}\n")


# Main function to process the daily notes
def main(config):
    client = OpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
    )
    notes_file = os.path.expanduser(config["daily_notes_file"])
    notes = load_notes(notes_file)

    today_notes = extract_today_notes(notes)

    if not today_notes:
        print("No notes found for today.")
        return

    # Use GPT-4o to summarize notes and identify tasks
    result = summarize_notes_and_identify_tasks(client, config["model"], today_notes)
    summary = result["summary"]
    tasks = result["tasks"]
    tags = result["tags"]

    print("Summary:")
    print(summary)
    print("Tags:")
    print(" ".join([f"#{tag}" for tag in tags]))
    print("Action Items:")
    for task in tasks:
        print(f"- {task}")
        add_to_reminders(task)

    # Prepare the folder structure
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    week_number = now.strftime("%U")
    date_str = now.strftime("%Y-%m-%d")
    output_dir = os.path.expanduser(
        f"{config['daily_output_dir']}/{year}/{month}/{week_number}"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{date_str}.md")

    # Write summary, tasks, and tags to a Markdown file
    write_summary_to_file(summary, tasks, tags, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Note Summarizer")
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to configuration file"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    main(config)
