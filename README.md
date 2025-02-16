# Daily Notes AI Summarization

This Python script is a note summarizer that processes daily, weekly, and meeting notes. It uses the OpenAI API to summarize notes, identify tasks, and maintain a semantic knowledge base.
It can extract action items and add them to the Apple Reminders App, extract learnings with auto-generated tags, and find semantically similar content across all your notes.
The script accepts several command-line arguments to customize its behavior.

## What does it do?

Based on timestamped notes in a single file it can:

- Generate a daily summary, including tags and actionable items
- Create a weekly summary (including accomplishments and learnings)
- Extract meeting notes
- Extract action items and add them to the Apple Reminders App
- Extract learnings and generate tags for each of the learnings
- Build and maintain a semantic knowledge base of your notes
- Find related content across all your notes using semantic search

_Please note_

This script has been entirely created by CodeLLama, GPT-4, and Claude 3.5 Sonnet.

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

`python main.py notes --skip-reminders --dry-run`

This would be the generated output:

---

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

---

The items extracted to action items will be added to Apple Reminders with a deadline of next morning 0900.

## Prerequisites

- Python 3.x
- OpenAI API key
- Apple Reminders

## Installation

1. Clone the repository.
2. Install the required Python packages: `pip install -r requirements.txt`.
3. Configure the script by editing the `config.yaml` file.

## Configuration

Copy `config.template.yml` to `config.yml` and setup the correct values.
Here is a brief explanation of each configuration item:

- `notes_base_dir`: Base directory containing all your notes. For example, `"~/Documents/notes"`.

- `knowledge_base`: Settings for scanning and processing notes:
  ```yaml
  exclude_patterns: 
    - "*.excalidraw.md"  # Exclude Excalidraw files
    - "templates/*"       # Exclude template directory
    - ".obsidian/*"      # Exclude Obsidian config
    - ".trash/*"         # Exclude trash
    - ".git/*"           # Exclude git directory
  ```

- `vector_store`: Configuration for the semantic knowledge base:
  - `path`: Location to store the vector database. For example, `"~/Documents/notes/.vector_store"`.
  - `chunk_size_min`: Minimum size of text chunks for semantic analysis (default: 50).
  - `chunk_size_max`: Maximum size of text chunks for semantic analysis (default: 500).
  - `similarity_threshold`: Minimum similarity score for matching content (default: 0.85).

Plus the standard configuration for note processing:
- `daily_notes_file`: Source file for daily notes
- `daily_output_dir`: Directory for processed daily notes
- `weekly_output_dir`: Directory for weekly summaries
- `meeting_notes_output_dir`: Directory for meeting notes
- `api_key`: OpenAI API key
- `model`: OpenAI model to use (e.g., "gpt-4")
- `learnings_file`: Source file for learnings
- `learnings_output_dir`: Directory for processed learnings

## Usage

The script now has two main command groups:

### Notes Processing Commands

Process daily notes, weekly summaries, and learnings:

```bash
# Process daily notes
python main.py notes --date 2024-02-16 --dry-run

# Generate weekly summary
python main.py notes --weekly --replace-summary

# Process meeting notes
python main.py notes --meetingnotes

# Process learnings
python main.py notes --process-learnings
```

### Knowledge Base Commands

Manage and query your semantic knowledge base:

```bash
# Reindex all notes (with dry run)
python main.py kb --reindex --dry-run

# Search for content
python main.py kb --query "python async programming" --limit 10

# Show connections for a note
python main.py kb --show-connections "path/to/note.md"

# Show connections as a Mermaid graph
python main.py kb --show-connections "path/to/note.md" --graph

# Find notes by tag
python main.py kb --find-by-tag "programming"

# Find notes by date
python main.py kb --find-by-date "2024-02-16"

# Show note's semantic structure
python main.py kb --note-structure "path/to/note.md"

# Search within specific note type
python main.py kb --query "meeting agenda" --note-type "meeting"
```

### Common Options

These options can be used with any command:

- `--config`: Specify config file (default: config.yaml)
- `--dry-run`: Show what would happen without making changes
- `--limit N`: Maximum number of results to return (default: 5)

## Cron

You can set up cron jobs to run the script automatically:

```bash
# Process daily notes at 6 PM
0 18 * * * /usr/bin/python3 /path/to/script.py notes

# Update knowledge base at midnight
0 0 * * * /usr/bin/python3 /path/to/script.py kb --reindex
```

## Future Improvements

- Add mail functionality to send summaries
- Add support for processing URLs and their content
- Add support for processing emails into notes
- Add automatic metadata extraction
- Add support for bi-directional linking
- Add support for timeline views
- Add support for knowledge graph visualization
