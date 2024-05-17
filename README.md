# Daily Notes AI Summarization

This Python script is a note summarizer that processes daily, weekly, and meeting notes. It uses the OpenAI API to summarize notes and identify tasks. The script accepts several command-line arguments to customize its behavior. 

## What does it do?

Based on timestamped notes in a single file it can generate

- A daily summary, including tags and actionable items
- A weekly summary (including accomplishments and learnings)
- Extract meeting notes 
- Extract action items and add them to the Apple Reminders App.

_Please note_

This script has been entirely created by CodeLLama and GPT-4o 

## Why this script

This script allows me to summarize my day, identify action items and add them to my reminders, so I can keep track of what I need to do.
I use jrnl (https://jrnl.sh/) to write daily notes during my work day, it's easy and entirely terminal based, which allows for quickly jotting down ideas, notes, quotes and report meetings. I have configured an alias for jrnl, called `daily` which opens neovim and adds everything I jot down to a single file prefixed with a timestamp. This is the jrnl config I use:

```yaml
   1   │ colors:
   2   │   body: none
   3   │   date: black
   4   │   tags: yellow
   5   │   title: cyan
   6   │ default_hour: 9
   7   │ default_minute: 0
   8   │ editor: nvim -f
   9   │ encrypt: false
  10   │ highlight: true
  11   │ indent_character: "|"
  12   │ journals:
  13   │   daily:
  14   │     journal: ~/Documents/notes/jrnl/daily.md
  15   │   default:
  16   │     journal: ~/Documents/notes/jrnl/journal.md
  19   │   idea:
  20   │     journal: ~/Documents/notes/jrnl/ideas.md
  23   │ linewrap: 79
  24   │ tagsymbols: "#@"
  25   │ template: false
  26   │ timeformat: "%F %r"
  27   │ version: v4.1
```

The zsh-alias to quickly start a daily note;

```
alias daily="jrnl daily"
```

At the end of the day the file containing notes would look like this:

```
[2024-05-18 08:45:32 AM] started the day by reviewing the sprint backlog. Identified key tasks to tackle using Trello.

[2024-05-18 11:12:09 AM] debugged the API integration issues with the new payment gateway.

[2024-05-18 12:30:44 PM] had a quick sync with the UX team to finalize the design for the new dashboard feature.

[2024-05-18 02:15:20 PM] attended the bi-weekly planning meeting. Discussed the priorities for the next sprint.

[2024-05-18 03:47:18 PM] researched optimization techniques for the search algorithm. Found some promising approaches using Elasticsearch.

[2024-05-18 04:25:51 PM] created a prototype for the new notification system. Need to test it with real user data next week.

[2024-05-18 05:08:33 PM] updated the project documentation to reflect the recent changes in the architecture.

[2024-05-18 06:22:54 PM] set up automated tests for the new microservices. This should help catch issues earlier in the development cycle.

[2024-05-18 06:45:10 PM] ended the day by reviewing PRs and providing feedback to the team.

[2024-05-19 09:10:13 AM] started the morning with a team stand-up meeting. Discussed blockers and progress.

[2024-05-19 10:55:48 AM] worked on refactoring the legacy codebase to improve maintainability.

[2024-05-19 12:15:30 PM] joined a webinar on the latest trends in AI and machine learning. Took notes for later review.
```
If you'd use the script on this journal like this:

`python main.py --skip-reminders --dry-run`

This would be the generated output:

----------------

## Summary

[08:45:32 AM] Reviewed sprint backlog and identified key tasks using Trello. 

[11:12:09 AM] Debugged API integration issues with new payment gateway. 

[12:30:44 PM] Synced with UX team to finalize dashboard feature design. 

[02:15:20 PM] Discussed next sprint priorities in bi-weekly planning meeting. 

[03:47:18 PM] Researched search algorithm optimization techniques using Elasticsearch. 

[04:25:51 PM] Created prototype for new notification system; planning to test with real user data next week. 

[05:08:33 PM] Updated project documentation to reflect recent architecture changes. 

[06:22:54 PM] Set up automated tests for new microservices to catch issues earlier in development. 

[06:45:10 PM] Reviewed PRs and provided feedback to team.

## Tags:
#sprint_backlog #api_integration #ux_design #sprint_planning #search_optimization #notification_system #project_documentation #automated_testing #code_review

## Action Items:
- Test the new notification system with real user data next week.

------

The items extracted to action items will be added to Apple Reminders with a deadline of next morning 0900.

## Prerequisites

- Python 3.x
- OpenAI API key
- Apple Reminders

## Installation

1. Clone the repository.
2. Install the required Python packages: `pip install -r requirements.txt`.
3. Set up your OpenAI API key as an environment variable: `export OPENAI_API_KEY=<your-api-key>`.
4. Configure the script by editing the `config.yaml` file.

## Configuration

Copy `config.template.yml` to `config.yml` and setup the correct values.
Here is a brief explanation of each configuration item:

- `daily_notes_file`: This is the path to the file where your daily notes are stored. The script will read from this file when processing daily notes. For example, `"~/Documents/notes/jrnl/daily.md"`.

- `daily_output_dir`: This is the directory where the script will save the processed daily notes. For example, `"~/Documents/notes/daily"`.

- `weekly_output_dir`: This is the directory where the script will save the processed weekly notes. For example, `"~/Documents/notes/Weekly"`.

- `meeting_notes_output_dir`: This is the directory where the script will save the processed meeting notes. For example, `"~/Documents/notes/meetingnotes"`.

- `base_url`: This is the (optional) base URL for the OpenAI API. The script will send requests to this URL to interact with the API. For example, `"https://api.openai.com/v1/"`.

- `api_key`: This is your OpenAI API key. The script will use this key to authenticate with the OpenAI API. 

- `model`: This is the model that the script will use for the OpenAI API. For example, `"gpt-4o"`.


## Usage

Here is a brief explanation of each argument:

- `--config`: This argument is used to specify the path to the configuration file. The default value is `config.yaml`.

- `--weekly`: If this argument is provided, the script will process weekly notes.

- `--dry-run`: If this argument is provided, the script will not write to files or create reminders. It's useful for testing the script without making changes.

- `--skip-reminders`: If this argument is provided, the script will not create reminders.

- `--replace-summary`: If this argument is provided, the script will replace the existing summary instead of appending to it.

- `--meetingnotes`: If this argument is provided, the script will generate and save meeting notes.

Here is an example of how to run the script with some arguments:

```bash
python main.py --config my_config.yaml --weekly --dry-run
```

In this example, the script will process weekly notes using the configuration file `my_config.yaml`, and it will not write to files or create reminders because the `--dry-run` argument is provided.

## Cron

You can set up a cron job to run this script at the end of each day. Here’s how to add a cron job on a Unix-based system:

```bash
crontab -e
```

Add this line to the file:

```bash
0 18 * * * /usr/bin/python3 /path/to/the/script.py
```

This cron job will run the script daily at 6 PM.

## Future Improvements

- Add mail functionality to send the summary and action items to an email address.
- Add support for a vector search API to search for related notes in order to link them
