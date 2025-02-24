"""Service for managing and analyzing links between notes."""

import logging
import os
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LinkService:
    """Manages link relationships and suggestions between notes."""

    def __init__(self, vector_store, chunking_service=None, embedding_service=None):
        """
        Initialize the link service.

        Args:
            vector_store: Instance of VectorStoreService for content queries
        """
        self.vector_store = vector_store
        self.chunking_service = chunking_service or vector_store.chunking_service
        self.embedding_service = embedding_service or vector_store.embedding_service
        self.base_path = os.path.expanduser(
            vector_store.config.get("path", "~/Documents/notes")
        )
        self.base_path = os.path.dirname(
            self.base_path
        )  # Get parent directory of .vector_store

    def analyze_relationships(self, note_id: str) -> Dict[str, Any]:
        """
        Analyze relationships for a specific note.

        Args:
            note_id: ID of the note to analyze

        Returns:
            Dictionary containing relationship analysis
        """
        # Normalize the path
        note_id = os.path.normpath(note_id)
        # Convert absolute path to relative if it's under the notes directory
        config = self.vector_store.config
        base_dir = os.path.basename(config.get("notes_base_dir", "~/Documents/notes"))
        if f"{base_dir}/" in note_id:
            note_id = note_id.split(f"{base_dir}/")[-1]
        logger.info(f"Starting relationship analysis for note: {note_id}")

        # Get existing connections
        direct_links = self.vector_store.find_connected_notes(note_id)
        logger.info(f"Found {len(direct_links)} direct links")

        # Find semantic relationships
        note_content = self.vector_store.get_note_content(note_id)
        logger.info(f"Retrieved note content: {'Yes' if note_content else 'No'}")
        if note_content:
            semantic_links = self.vector_store.find_similar(
                query_embedding=note_content["embedding"], limit=5, threshold=0.6
            )
        else:
            semantic_links = []

        # Get backlinks
        backlinks = self._find_backlinks(note_id)

        return {
            "direct_links": direct_links,
            "semantic_links": semantic_links,
            "backlinks": backlinks,
            "suggested_links": self._suggest_connections(note_id, direct_links, backlinks),
        }

    def _find_backlinks(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Find all notes that link to this note.

        Args:
            note_id: ID of the note to find backlinks for

        Returns:
            List of notes linking to this note
        """
        return self.vector_store.find_backlinks(note_id)

    def _suggest_connections(
        self, note_id: str, existing_links: List[Dict[str, Any]] = None, backlinks: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest potential connections based on content similarity.

        Args:
            note_id: ID of the note to find suggestions for
            existing_links: Optional list of existing direct links to avoid duplicate calls
            backlinks: Optional list of backlinks to avoid duplicate calls

        Returns:
            List of suggested connections
        """
        # Get note content
        note_content = self.vector_store.get_note_content(note_id)
        if not note_content:
            logger.warning(f"Could not get content for note: {note_id}")
            return []

        # Find similar content with lower threshold for suggestions
        similar = self.vector_store.find_similar(
            query_embedding=note_content["embedding"],
            limit=10,  # Increased limit to find more potential matches
            threshold=0.5,  # Lower threshold for suggestions
        )

        logger.info(f"Found {len(similar)} similar documents for {note_id}")

        # Get existing connections including backlinks
        existing = set()
        direct_links = existing_links or self.vector_store.find_connected_notes(note_id)
        backlinks = backlinks or self.vector_store.find_backlinks(note_id)

        # Add both direct links and backlinks to existing set
        existing.update(link["target_id"] for link in direct_links)
        existing.update(link["source_id"] for link in backlinks)

        logger.info(f"Found {len(existing)} existing connections")

        # Group results by note_id and calculate aggregate scores
        note_matches = {}
        for result in similar:
            result_id = result["metadata"].get("doc_id")
            # Skip self-links and already existing links
            if (
                result_id
                and result_id not in existing
                and result_id != note_id
                and os.path.normpath(result_id) != os.path.normpath(note_id)
            ):
                if result_id not in note_matches:
                    note_matches[result_id] = {
                        "note_id": result_id,
                        "max_similarity": result["similarity"],
                        "chunk_similarities": [result["similarity"]],
                        "best_preview": result["content"][:200].replace("\n", " ").strip(),
                        "chunk_count": 1
                    }
                else:
                    match = note_matches[result_id]
                    match["chunk_similarities"].append(result["similarity"])
                    match["chunk_count"] += 1
                    if result["similarity"] > match["max_similarity"]:
                        match["max_similarity"] = result["similarity"]
                        match["best_preview"] = result["content"][:200].replace("\n", " ").strip()

        # Calculate aggregate scores and create final suggestions
        suggestions = []
        for note_id, match in note_matches.items():
            # Calculate aggregate score that rewards multiple chunks
            # We use a combination of:
            # 1. The maximum similarity of any chunk
            # 2. A bonus based on number of chunks and their similarities
            chunk_bonus = sum(match["chunk_similarities"]) / len(match["chunk_similarities"]) * min(1, match["chunk_count"] / 3)
            aggregate_score = match["max_similarity"] + (chunk_bonus * 0.2)  # Adjust bonus weight as needed

            suggestions.append({
                "note_id": note_id,
                "similarity": round(aggregate_score, 3),
                "reason": f"Content similarity ({match['max_similarity']:.2f}) with {match['chunk_count']} matching chunks",
                "preview": match["best_preview"]
            })
            logger.debug(
                f"Added suggestion: {note_id} with aggregate score {aggregate_score:.3f} from {match['chunk_count']} chunks"
            )

        # Sort suggestions by aggregate score
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)

        logger.info(f"Generated {len(suggestions)} suggestions for {note_id}")
        return suggestions

    def update_obsidian_links(
        self, note_path: str, links: List[Dict[str, Any]], update_backlinks: bool = True, skip_vector_update: bool = False
    ) -> None:
        """
        Update Obsidian-style wiki links in a note file.

        Args:
            note_path: Full path to the note file
            links: List of links to add/update
            update_backlinks: Whether to update backlinks in target notes
            skip_vector_update: Whether to skip updating the vector store (useful for batch operations)

        Raises:
            FileNotFoundError: If the note file does not exist
            IOError: If there is an error reading or writing the file
        """
        # Ensure we have the full path
        note_path = os.path.expanduser(note_path)

        # Get relative ID for vector store
        note_id = note_path
        base_dir = os.path.basename(self.vector_store.config.get("notes_base_dir", "~/Documents/notes"))
        if f"{base_dir}/" in note_path:
            note_id = note_path.split(f"{base_dir}/")[-1]

        try:
            # Read the entire file first
            with open(note_path, "r") as f:
                original_content = f.read()

            # Split content at horizontal line if it exists
            if "\n---\n" in original_content:
                content_parts = original_content.split("\n---\n", 1)
                main_content = content_parts[0]
                links_section = content_parts[1] if len(content_parts) > 1 else ""
            else:
                main_content = original_content
                links_section = ""

            # Process links to add
            new_links = []
            for link in links:
                if link.get("add_wiki_link"):
                    target = link["target_id"]
                    alias = self._generate_alias(target)  # Always generate an alias
                    new_link = f"[[{target}|{alias}]]"

                    # Check if link already exists in either section
                    if not self._has_wiki_link(main_content + links_section, target):
                        new_links.append(new_link)

                        # Update backlinks in target note if requested
                        if update_backlinks:
                            self._update_target_backlinks(target, note_id, note_path)

            if new_links:
                # Construct updated content while preserving both sections
                updated_content = main_content.rstrip()

                # If we have existing links section, preserve it and add new links
                if links_section:
                    updated_content += "\n---\n" + links_section.rstrip()
                    # Add header and new links if they don't exist
                    if "## Auto generated references" not in updated_content:
                        updated_content += "\n\n## Auto generated references"
                    # Add new links at the end of existing links section
                    for link in new_links:
                        updated_content += f"\n{link}"
                else:
                    # No existing links section, create new one with header
                    updated_content += "\n\n---\n## Auto generated references"
                    for link in new_links:
                        updated_content += f"\n{link}"

                # Write changes to the file
                with open(note_path, "w") as f:
                    logger.info(f"Writing changes to file: {note_path}")
                    f.write(updated_content)
                logger.info(f"Updated links in file: {note_path}")

                # Update the vector store if not skipped
                if not skip_vector_update:
                    self._update_vector_store(note_id, updated_content)
            else:
                logger.info(f"No new links to add for: {note_path}")

        except FileNotFoundError as e:
            logger.error(f"Error reading file {note_path}: {str(e)}")
            raise
        except IOError as e:
            logger.error(f"Error accessing file {note_path}: {str(e)}")
            raise

    def _generate_alias(self, target: str) -> str:
        """Generate a readable alias from the target ID."""
        # Just use the filename without extension
        return os.path.basename(target).replace(".md", "")

    def _has_wiki_link(self, content: str, target: str) -> bool:
        """
        Check if content already contains a wiki link to target.

        Args:
            content: The note content to check
            target: The target note ID to look for

        Returns:
            bool: True if the link already exists
        """
        # Check for exact wiki link match
        exact_pattern = rf"\[\[{re.escape(target)}(?:\|[^\]]+)?\]\]"
        if re.search(exact_pattern, content):
            logger.debug(f"Found exact wiki link match for {target}")
            return True

        # Check for link in any section
        sections = ["## Related", "## Links", "## References", "## Backlinks"]
        for section in sections:
            if section in content:
                section_content = content.split(section, 1)[1].split("\n\n")[0]
                if target in section_content:
                    logger.debug(f"Found {target} in {section} section")
                    return True

        # Check for any mention of the target file name
        base_name = os.path.basename(target).replace(".md", "")
        if f"[[{base_name}" in content:
            logger.debug(f"Found mention of {base_name} in content")
            return True

        return False

    def _insert_wiki_link(self, content: str, new_link: str) -> str:
        """Insert a wiki link at the bottom of the document."""
        # Check if we already have a horizontal line separator
        if "\n---\n" not in content:
            # Add horizontal line and links section
            return f"{content.rstrip()}\n\n---\n{new_link}"
        else:
            # Add to existing links section after the horizontal line
            parts = content.rsplit("\n---\n", 1)
            return f"{parts[0]}\n---\n{parts[1].rstrip()}\n{new_link}"

    def _remove_wiki_link(self, content: str, target: str) -> str:
        """Remove a wiki link from the content."""
        pattern = rf"\[\[{re.escape(target)}(?:\|[^\]]+)?\]\]\n?"
        return re.sub(pattern, "", content)

    def _update_target_backlinks(
        self, target_id: str, source_id: str, source_path: str
    ) -> None:
        """
        Update backlinks in a target note.

        Args:
            target_id: ID of the target note
            source_id: ID of the source note
            source_path: Path to the source note
        """
        # Get target note content
        note_content = self.vector_store.get_note_content(target_id)
        if not note_content:
            logger.warning(f"Could not get content for note: {target_id}")
            return

        # Read the current content
        try:
            with open(source_path, "r") as f:
                content = f.read()
        except IOError as e:
            logger.error(f"Error reading file {source_path}: {str(e)}")
            return

        # Add backlink if it doesn't exist
        if f"[[{source_id}]]" not in content:
            # Add backlink at the end of the file
            if not content.endswith("\n"):
                content += "\n"
            content += f"\n[[{source_id}]]\n"

            # Write updated content
            try:
                with open(source_path, "w") as f:
                    f.write(content)
            except IOError as e:
                logger.error(f"Error writing file {source_path}: {str(e)}")

    def _update_vector_store(self, note_id: str, content: str) -> None:
        """
        Update the vector store for a note.

        Args:
            note_id: ID of the note to update
            content: New content of the note
        """
        try:
            chunks = self.vector_store.chunking_service.chunk_document(
                content, doc_type="note"
            )
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = self.vector_store.embedding_service.embed_chunks(
                chunk_texts
            )
            self.vector_store.update_document(
                doc_id=note_id, new_chunks=chunk_texts, new_embeddings=embeddings
            )
            logger.info(f"Updated vector store for: {note_id}")
        except Exception as e:
            logger.error(f"Failed to update vector store for {note_id}: {str(e)}")
