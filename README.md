# Daily Auto Tasks

This is a Python script that processes daily notes, summarizes them, identifies action items, and adds them to Apple Reminders. It also writes a summary and action items to a Markdown file.

## Why this script

I use jrnl (https://jrnl.sh/) to write daily notes during my work day, it's easy and entirely terminal based, which allows for quickly jotting down ideas, notes, quotes and report meetings.
This script allows me to summarize my day, identify action items and add them to my reminders, so I can keep track of what I need to do.

## Prerequisites

- Python 3.x
- OpenAI API key
- Apple Reminders

## Installation

1. Clone the repository.
2. Install the required Python packages: `pip install -r requirements.txt`.
3. Set up your OpenAI API key as an environment variable: `export OPENAI_API_KEY=<your-api-key>`.
4. Configure the script by editing the `config.yaml` file.

## Usage

Run the script using the following command:

```bash
python main.py --config config.yaml

```
