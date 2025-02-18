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
- OpenAI API key (if using OpenAI embeddings)
- Apple Reminders

### Optional Dependencies (based on embedding model choice)

For OpenAI embeddings (default):

- OpenAI API key
- `pip install openai`

For HuggingFace models:

- `pip install sentence-transformers`
- CUDA-capable GPU (optional, for faster processing)

For Cohere embeddings:

- Cohere API key
- `pip install cohere`

For Ollama (local models):

1. Install Ollama:
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh
   ```
2. Start the Ollama service:
   ```bash
   ollama serve
   ```
3. Pull your desired embedding model:

   ```bash
   # For general text embeddings
   ollama pull nomic-embed-text

   # For code-specific embeddings
   ollama pull codellama
   ```

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
    - "*.excalidraw.md" # Exclude Excalidraw files
    - "templates/*" # Exclude template directory
    - ".obsidian/*" # Exclude Obsidian config
    - ".trash/*" # Exclude trash
    - ".git/*" # Exclude git directory
  ```

- `vector_store`: Configuration for the semantic knowledge base:

  - `path`: Location to store the vector database. For example, `"~/Documents/notes/.vector_store"`.
  - `chunk_size_min`: Minimum size of text chunks for semantic analysis (default: 50).
  - `chunk_size_max`: Maximum size of text chunks for semantic analysis (default: 500).
  - `similarity_threshold`: Minimum similarity score for matching content. This value depends on your embedding model:
    - For normalized embeddings (OpenAI, HuggingFace): Use 0.60-0.85 (higher = stricter matching)
    - For distance-based embeddings (some Ollama models): Use negative values like -250.0 (less negative = stricter matching)
  - `hnsw_config`: HNSW index settings for ChromaDB:
    - `ef_construction`: Controls index build quality (default: 400)
    - `ef_search`: Controls search quality (default: 200)
    - `m`: Number of connections per element (default: 128)

- `embeddings`: Configuration for text embedding models:
  - `model_type`: Type of embedding model to use. Options:
    - `"openai"`: OpenAI's embedding models (requires API key)
    - `"huggingface"`: Local HuggingFace models
    - `"huggingface_instruct"`: HuggingFace instruction-tuned models
    - `"cohere"`: Cohere's embedding models (requires API key)
    - `"ollama"`: Local Ollama models
  - `model_name`: Name of the specific model to use (examples below)
  - `batch_size`: Number of texts to embed at once (default: 100)
  - `model_kwargs`: Optional model-specific settings:
    - `device`: For HuggingFace models: "cpu" or "cuda"
    - `normalize_embeddings`: Whether to normalize embeddings (default: true)
  - `ollama_config`: Settings for Ollama models:
    - `base_url`: Ollama API URL (default: "http://localhost:11434")
    - `num_ctx`: Context window size (default: 512)
    - `num_thread`: Number of threads to use (default: 4)

Example configurations for different embedding models:

```yaml
# OpenAI (default, normalized embeddings)
embeddings:
  model_type: "openai"
  model_name: "text-embedding-3-small"
  batch_size: 100
vector_store:
  similarity_threshold: 0.60  # Higher = stricter matching
search:
  thresholds:
    default: 0.60
    tag_search: 0.50
    date_search: 0.50

# Ollama with mxbai-embed-large (distance-based)
embeddings:
  model_type: "ollama"
  model_name: "mxbai-embed-large:latest"
  batch_size: 100
  ollama_config:
    base_url: "http://localhost:11434"
    num_ctx: 512
    num_thread: 4
vector_store:
  similarity_threshold: -250.0  # Less negative = stricter matching
search:
  thresholds:
    default: -250.0
    tag_search: -300.0  # More lenient for tag searches
    date_search: -300.0  # More lenient for date searches

# Local HuggingFace model (normalized)
embeddings:
  model_type: "huggingface"
  model_name: "sentence-transformers/all-mpnet-base-v2"
  batch_size: 32
  model_kwargs:
    device: "cuda"
    normalize_embeddings: true
vector_store:
  similarity_threshold: 0.70  # Adjust based on model performance
```

### Important Notes About Similarity Thresholds

Different embedding models use different similarity metrics:

1. **Normalized Embeddings** (OpenAI, most HuggingFace models):

   - Use cosine similarity scores between 0 and 1
   - Higher thresholds (e.g., 0.85) mean stricter matching
   - Lower thresholds (e.g., 0.50) mean more lenient matching
   - Common range: 0.60-0.85

2. **Distance-Based Embeddings** (some Ollama models like mxbai-embed-large):
   - Use negative distance scores (more negative = more different)
   - Less negative thresholds (e.g., -200.0) mean stricter matching
   - More negative thresholds (e.g., -300.0) mean more lenient matching
   - Common range: -200.0 to -300.0

When switching embedding models:

1. Check if your model uses normalized or distance-based similarity
2. Adjust thresholds accordingly in both `vector_store` and `search` settings
3. Delete the existing vector store and reindex:
   ```bash
   rm -rf ~/Documents/notes/.vector_store
   python main.py kb --reindex
   ```
4. Test with different threshold values to find the best balance for your content

Plus the standard configuration for note processing:

- `daily_notes_file`: Source file for daily notes
- `daily_output_dir`: Directory for processed daily notes
- `weekly_output_dir`: Directory for weekly summaries
- `meeting_notes_output_dir`: Directory for meeting notes
- `api_key`: OpenAI API key
- `model`: OpenAI model to use (e.g., "gpt-4")
- `learnings_file`: Source file for learnings
- `learnings_output_dir`: Directory for processed learnings

## Important Note About Changing Embedding Models

When changing the embedding model configuration, you must reindex your knowledge base to ensure consistency. Different models produce different embedding vectors, which are not compatible with each other. To reindex:

1. Delete the existing vector store:

   ```bash
   rm -rf ~/Documents/notes/.vector_store  # Adjust path based on your config
   ```

2. Reindex your notes:
   ```bash
   python main.py kb --reindex
   ```

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

# Update only modified notes (faster than full reindex)
python main.py kb --update

# Analyze and auto-link all notes
python main.py kb --analyze-all --auto-link

# Analyze and auto-link only recently modified notes
python main.py kb --analyze-updated --auto-link

# Analyze links for a specific note
python main.py kb --analyze-links "path/to/note.md" --auto-link

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

## Knowledge Base Management

The script maintains a semantic knowledge base of your notes using vector embeddings. You can:

- Reindex all notes using `--reindex`
- Update only modified notes using `--update` (faster than full reindex)
- Search for similar content across all notes
- View note connections and relationships
- Find notes by tags or dates
- Analyze note structure
- Automatically discover and add semantic links between notes
- Maintain backlinks between connected notes
- Generate readable aliases for wiki-links

The `--update` command checks file modification times and only processes notes that have changed since they were last indexed, making it much faster than a full reindex.

### Link Management

The script can automatically analyze and manage links between your notes:

- Discover semantic relationships between notes based on content similarity
- Add wiki-links with readable aliases
- Maintain backlinks in target notes
- Update only modified notes to avoid unnecessary processing
- Place links in appropriate sections (Related, Links, References)
- Handle both forward links and backlinks consistently

Use `--analyze-links` for a single note or `--analyze-all`/`--analyze-updated` for batch processing. Add `--auto-link` to automatically add suggested links without prompting.

## Future Improvements

- Add mail functionality to send summaries
- Add support for processing URLs and their content
- Add support for processing emails into notes
- Add automatic metadata extraction
- Add support for bi-directional linking
- Add support for timeline views
- Add support for knowledge graph visualization
