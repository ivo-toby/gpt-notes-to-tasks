"""
Note processing and summarization tool.

This module provides functionality for processing daily notes, weekly summaries,
meeting notes and learning entries. It interfaces with various services to
generate summaries, extract tasks, and manage reminders.
"""

from services.learning_service import LearningService
from services.summary_service import SummaryService
from services.meeting_service import MeetingService
from services.openai_service import OpenAIService
from services.vector_store import VectorStoreService, EmbeddingService, ChunkingService
from utils.config_loader import load_config
from utils.cli import setup_argparser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_daily_notes(cfg, cli_args):
    """
    Process daily notes to generate summaries and extract tasks.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    summary_service = SummaryService(cfg)
    summary_service.process_daily_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run,
        skip_reminders=cli_args.skip_reminders,
        replace_summary=cli_args.replace_summary
    )


def process_weekly_notes(cfg, cli_args):
    """
    Process and generate weekly note summaries.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    summary_service = SummaryService(cfg)
    summary_service.process_weekly_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run,
        replace_summary=cli_args.replace_summary
    )


def process_meeting_notes(cfg, cli_args):
    """
    Process daily notes to generate structured meeting notes.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    meeting_service = MeetingService(cfg)
    meeting_service.process_meeting_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run
    )


def process_new_learnings(cfg, cli_args):
    """
    Process and extract new learnings from notes.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    learning_service = LearningService(
        cfg["learnings_file"], cfg["learnings_output_dir"]
    )
    learning_service.process_new_learnings(
        OpenAIService(api_key=cfg["api_key"], model=cfg["model"])
    )


def process_vector_store(cfg, cli_args):
    """
    Process and index notes in the vector store.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    try:
        vector_store = VectorStoreService(cfg)
        embedding_service = EmbeddingService(cfg)
        chunking_service = ChunkingService(cfg)

        if cli_args.reindex:
            logger.info("Reindexing all notes...")
            # Get all notes from the summary service
            summary_service = SummaryService(cfg)
            notes = summary_service.get_all_notes()

            for note in notes:
                if cli_args.dry_run:
                    logger.info(f"Would process note: {note['id']}")
                    continue

                chunks = chunking_service.chunk_document(note['content'])
                chunk_texts = [chunk['content'] for chunk in chunks]
                embeddings = embedding_service.embed_chunks(chunk_texts)
                
                # Add metadata from the note
                metadata = {
                    'source': note.get('source', 'unknown'),
                    'date': note.get('date', ''),
                    'type': note.get('type', 'note')
                }
                
                vector_store.add_document(
                    doc_id=note['id'],
                    chunks=chunk_texts,
                    embeddings=embeddings,
                    metadata=metadata
                )

        elif cli_args.query:
            # Search for similar content
            query_embedding = embedding_service.embed_text(cli_args.query)
            results = vector_store.find_similar(
                query_embedding=query_embedding,
                limit=cli_args.limit or 5,
                threshold=cfg['vector_store'].get('similarity_threshold', 0.85)
            )

            print("\nSearch Results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Similarity: {result['similarity']:.2f}")
                print(f"Source: {result['metadata'].get('source', 'unknown')}")
                print(f"Content: {result['content'][:200]}...")

    except Exception as e:
        logger.error(f"Error processing vector store: {str(e)}")
        raise


if __name__ == "__main__":
    parser = setup_argparser()
    args = parser.parse_args()

    cfg = load_config(args.config)
    
    if args.process_learnings:
        process_new_learnings(cfg, args)
    elif args.meetingnotes:
        process_meeting_notes(cfg, args)
    elif args.weekly:
        process_weekly_notes(cfg, args)
    elif args.vector_store:
        process_vector_store(cfg, args)
    else:
        process_daily_notes(cfg, args)
        process_meeting_notes(cfg, args)
        process_new_learnings(cfg, args)
