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

This script has been entirely created by CodeLLama, GPT-4o, Claude 3.5 Sonnet and Gemini 2 Flash using Anthropic MCP, Cursor and aider.chat.

## Getting Started

This guide will help you set up and run the script safely with your notes.

### 1. Prepare Your Notes Repository

First, set up a Git repository for your notes (recommended):

```bash
# Create a new directory for your notes
mkdir ~/Documents/notes
cd ~/Documents/notes

# Initialize git repository
git init

# Create basic structure
mkdir daily weekly meetingnotes learnings
touch .gitignore

# Add recommended entries to .gitignore
cat << EOF > .gitignore
.vector_store/
.obsidian/
.trash/
*.excalidraw.md
.DS_Store
EOF

# Initial commit
git add .
git commit -m "Initial notes structure"
```

### 2. Install Dependencies

1. Clone this tool repository:

   ```bash
   git clone https://github.com/yourusername/gpt-notes-to-tasks.git
   cd gpt-notes-to-tasks
   ```

2. Create and activate a virtual environment:

   ```bash
   # Using venv (recommended)
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Install embedding model dependencies (choose one):

   ```bash
   # For OpenAI (default)
   pip install openai

   # For local models with Ollama (recommended for privacy)
   # First install Ollama
   curl https://ollama.ai/install.sh | sh
   # Start Ollama service
   ollama serve
   # Pull embedding model
   ollama pull nomic-embed-text
   ```

### 3. Configure the Tool

1. Create your configuration:

   ```bash
   # Copy template
   cp config.template.yaml config.yaml
   ```

2. Edit `config.yaml` with your settings:

   ```yaml
   # Essential settings
   notes_base_dir: "~/Documents/notes" # Your notes directory
   daily_notes_file: "~/Documents/notes/daily/daily.md"
   daily_output_dir: "~/Documents/notes/daily"
   weekly_output_dir: "~/Documents/notes/weekly"
   meeting_notes_output_dir: "~/Documents/notes/meetingnotes"
   learnings_file: "~/Documents/notes/learnings/learnings.md"
   learnings_output_dir: "~/Documents/notes/learnings"

   # For OpenAI
   api_key: "your-api-key" # Required for OpenAI embeddings
   model: "gpt-4" # or gpt-3.5-turbo for lower cost

   # For local embeddings (recommended)
   embeddings:
     model_type: "ollama"
     model_name: "nomic-embed-text"
     ollama_config:
       base_url: "http://localhost:11434"
       num_ctx: 512
       num_thread: 4
   ```

### 4. First Run

1. Test with dry run (safe, no changes):

   ```bash
   # Test daily notes processing
   python main.py notes --dry-run

   # Test knowledge base indexing
   python main.py kb --reindex --dry-run
   ```

2. Initialize knowledge base:

   ```bash
   # Build initial index
   python main.py kb --reindex
   ```

3. Test search functionality:
   ```bash
   # Try searching
   python main.py kb --query "test query"
   ```

### 5. Regular Usage

1. Set up daily note taking:

   ```bash
   # Add to your .zshrc or .bashrc
   alias daily="jrnl daily"  # If using jrnl
   # or
   alias daily="nvim ~/Documents/notes/daily/daily.md"
   ```

2. Recommended workflow:

   ```bash
   # Morning: Review yesterday's notes
   python main.py notes --date yesterday

   # Process specific date
   python main.py notes --date 2024-02-16

   # Process today's notes (default)
   python main.py notes

   # Weekly: Generate summary
   python main.py notes --weekly

   # Periodically: Update knowledge base
   python main.py kb --update
   ```

   The `--date` option accepts:

   - `yesterday` for the previous day
   - `today` for the current day (default)
   - A specific date in YYYY-MM-DD format (e.g., "2024-02-16")

3. Git backup routine:
   ```bash
   # Add to your daily routine
   cd ~/Documents/notes
   git add .
   git commit -m "Daily notes update: $(date '+%Y-%m-%d')"
   git push  # If using remote repository
   ```

### 6. Maintenance Best Practices

1. Regular backups:

   - Keep your notes in git
   - Consider using a private GitHub/GitLab repository
   - Regularly push changes

2. Vector store maintenance:

   ```bash
   # Monthly: Rebuild index to optimize
   rm -rf ~/Documents/notes/.vector_store
   python main.py kb --reindex
   ```

3. Monitor and adjust:
   - Watch similarity scores in search results
   - Adjust thresholds if needed
   - Keep dependencies updated

### 7. Troubleshooting

If you encounter issues:

1. Check logs:

   ```bash
   # Enable debug logging
   sed -i 's/level: "INFO"/level: "DEBUG"/' config.yaml
   ```

2. Verify embeddings:

   ```bash
   # Test embedding service
   python main.py kb --query "test" --debug
   ```

3. Common fixes:
   - Clear vector store: `rm -rf ~/Documents/notes/.vector_store`
   - Reindex: `python main.py kb --reindex`
   - Check Ollama service: `curl http://localhost:11434/api/embeddings`

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

### Performance Analysis: OpenAI vs Ollama mxbai-embed-large

We've conducted extensive testing comparing OpenAI's text-embedding-3-small with Ollama's mxbai-embed-large model. Here are our findings:

1. **Similarity Scores & Relevance**:
   - OpenAI embeddings: Scores typically range from 0.35-0.45
   - mxbai-embed-large: Scores typically range from 0.60-0.65
   - mxbai-embed-large showed better semantic understanding, especially for code snippets
   - Higher scores with mxbai-embed-large correlate with more relevant results

2. **Content Chunking Behavior**:
   - Current optimal settings:
     ```yaml
     chunking_config:
       recursive:
         chunk_size: 300  # Reduced for better focus
         chunk_overlap: 100  # Increased for context
         separators: ["\n\n", "\n### ", "\n## ", "\n# ", "\n", ". ", "? ", "! ", "; "]  # Respects document structure
     ```
   - These settings preserve code blocks and their context
   - Headers stay with their content
   - Natural breaks at paragraph and section boundaries

3. **Search Thresholds**:
   ```yaml
   search:
     thresholds:
       default: 0.35  # Base threshold for content matching
       tag_search: 0.30  # More lenient for tag matches
       date_search: 0.30  # More lenient for date matches
       content_search: 0.40  # Stricter for content searches
   ```

4. **Recommendations**:
   - mxbai-embed-large performs notably better for technical content
   - Local processing eliminates API costs and latency
   - Better handling of code snippets and documentation
   - More consistent chunking of technical content

5. **Vector Store Maintenance**:
   - Delete store and reindex when changing models:
     ```bash
     rm -rf ~/workspace/rd/cf-notes/.vector_store
     python main.py kb --reindex
     ```
   - Monitor similarity scores to detect any drift
   - Consider monthly reindexing for optimal performance



### Recommended Model Configuration

For optimal results with technical content and code snippets, we recommend using Ollama with mxbai-embed-large:

```yaml
# config.yaml
embeddings:
  model_type: "ollama"
  model_name: "mxbai-embed-large:latest"
  batch_size: 100
  ollama_config:
    base_url: "http://localhost:11434"
    num_ctx: 512
    num_thread: 4

chunking_config:
  recursive:
    chunk_size: 300
    chunk_overlap: 100
    separators: ["\n\n", "\n### ", "\n## ", "\n# ", "\n", ". ", "? ", "! ", "; "]

search:
  thresholds:
    default: 0.35
    tag_search: 0.30
    date_search: 0.30
    content_search: 0.40
```

To use this configuration:

1. Install Ollama:
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh
   ```

2. Start Ollama service:
   ```bash
   ollama serve
   ```

3. Pull the model:
   ```bash
   ollama pull mxbai-embed-large
   ```

4. Update your config.yaml with the above settings

5. Reindex your knowledge base:
   ```bash
   rm -rf ~/workspace/rd/cf-notes/.vector_store
   python main.py kb --reindex
   ```

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
