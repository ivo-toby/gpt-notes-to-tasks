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
        if "cf-notes/" in note_id:
            note_id = note_id.split("cf-notes/")[-1]
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

        return {
            "direct_links": direct_links,
            "semantic_links": semantic_links,
            "backlinks": self._find_backlinks(note_id),
            "suggested_links": self._suggest_connections(note_id),
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

    def _suggest_connections(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Suggest potential connections based on content similarity.

        Args:
            note_id: ID of the note to find suggestions for

        Returns:
            List of suggested connections
        """
        # Get note content
        note_content = self.vector_store.get_note_content(note_id)
        if not note_content:
            return []

        # Find similar content
        similar = self.vector_store.find_similar(
            query_embedding=note_content["embedding"], limit=10, threshold=0.6
        )

        # Filter out existing connections
        existing = set(
            link["target_id"]
            for link in self.vector_store.find_connected_notes(note_id)
        )
        suggestions = []

        for result in similar:
            result_id = result["metadata"].get("doc_id")
            # Skip self-links and already existing links
            if (result_id and 
                result_id not in existing and 
                result_id != note_id and
                os.path.normpath(result_id) != os.path.normpath(note_id)):
                suggestions.append(
                    {
                        "note_id": result_id,
                        "similarity": result["similarity"],
                        "reason": "Content similarity",
                        "preview": result["content"][:200],
                    }
                )

        return suggestions

    def update_obsidian_links(
        self, note_path: str, links: List[Dict[str, Any]], update_backlinks: bool = True
    ) -> None:
        """
        Update Obsidian-style wiki links in a note file.

        Args:
            note_path: Full path to the note file
            links: List of links to add/update
            update_backlinks: Whether to update backlinks in target notes
        """
        # Ensure we have the full path
        note_path = os.path.expanduser(note_path)

        # Get relative ID for vector store
        note_id = note_path
        if "cf-notes/" in note_path:
            note_id = note_path.split("cf-notes/")[-1]
        """
        Update Obsidian-style wiki links in a note.

        Args:
            note_id: ID of the note to update
            links: List of links to add/update
            update_backlinks: Whether to update backlinks in target notes
        """
        note_content = self.vector_store.get_note_content(note_id)
        if not note_content:
            logger.warning(f"Note not found: {note_id}")
            return

        content = note_content["content"]
        updated = False

        # Process each link
        for link in links:
            if link.get("add_wiki_link"):
                target = link["target_id"]
                alias = link.get("alias", self._generate_alias(target))
                new_link = f"[[{target}|{alias}]]"

                # Check if link already exists
                if not self._has_wiki_link(content, target):
                    # Add link in a semantically appropriate location
                    content = self._insert_wiki_link(content, new_link)
                    updated = True

                    # Update backlinks in target note if requested
                    if update_backlinks:
                        self._update_target_backlinks(target, note_id, note_path)

            elif link.get("remove_wiki_link"):
                # Remove existing link
                content = self._remove_wiki_link(content, link["target_id"])
                updated = True

        if updated:
            try:
                # Read existing content to verify changes
                with open(note_path, "r") as f:
                    original_content = f.read()
                    
                if original_content.strip() != content.strip():
                    # Write changes to the file
                    with open(note_path, "w") as f:
                        logger.info(f"Writing changes to file: {note_path}")
                        logger.debug(f"Original content length: {len(original_content)}")
                        logger.debug(f"New content length: {len(content)}")
                        f.write(content)
                    logger.info(f"Updated links in file: {note_path}")

                    # Update the vector store
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
                else:
                    logger.info(f"No content changes needed for: {note_path}")
            except IOError as e:
                logger.error(f"Error writing to file {note_path}: {str(e)}")
                raise

    def _generate_alias(self, target: str) -> str:
        """Generate a readable alias from the target ID."""
        # Remove file extension and path
        alias = os.path.basename(target).replace(".md", "")
        # Convert kebab/snake case to title case
        alias = " ".join(word.capitalize() for word in re.split(r"[-_]", alias))
        return alias

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
        """Insert a wiki link in a semantically appropriate location."""
        # Try to find a "Related" or "Links" section
        sections = ["## Related", "## Links", "## References"]
        
        # First try to find an existing section
        for section in sections:
            if section in content:
                # Split content at the section
                before_section, section_content = content.split(section, 1)
                
                # Find the next section if it exists
                next_section_start = len(section_content)
                for next_section in ["##"]:
                    pos = section_content.find(next_section)
                    if pos != -1:
                        next_section_start = pos
                
                # Insert the new link after the section header but before any existing content
                section_content_start = section_content[:next_section_start].strip()
                section_content_rest = section_content[next_section_start:]
                
                # Add the new link, preserving existing content
                updated_section = f"{section}\n{section_content_start}"
                if section_content_start:
                    updated_section += f"\n{new_link}"
                else:
                    updated_section += new_link
                
                # Reconstruct the full content
                return f"{before_section}{updated_section}{section_content_rest}"
        
        # If no appropriate section found, add to end with header
        # Ensure we preserve all existing content
        return f"{content.rstrip()}\n\n## Related\n{new_link}"

    def _remove_wiki_link(self, content: str, target: str) -> str:
        """Remove a wiki link from the content."""
        pattern = rf"\[\[{re.escape(target)}(?:\|[^\]]+)?\]\]\n?"
        return re.sub(pattern, "", content)

    def _update_target_backlinks(
        self, target_id: str, source_id: str, source_path: str
    ) -> None:
        """Update backlinks section in the target note."""
        target_content = self.vector_store.get_note_content(target_id)
        if not target_content:
            return

        content = target_content["content"]
        backlink = f"[[{source_id}]]"

        # Find or create backlinks section
        if "## Backlinks" not in content:
            content += f"\n\n## Backlinks\n{backlink}\n"
        else:
            # Add to existing backlinks section if not already present
            if backlink not in content:
                content = content.replace(
                    "## Backlinks\n", f"## Backlinks\n{backlink}\n"
                )

        try:
            # Get full path for target note using base path
            target_path = os.path.join(self.base_path, target_id)

            # Write changes to the target file
            with open(target_path, "w") as f:
                f.write(content)
            logger.info(f"Updated backlinks in file: {target_path}")

            # Update target note in vector store
            chunks = self.vector_store.chunking_service.chunk_document(
                content, doc_type="note"
            )
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = self.vector_store.embedding_service.embed_chunks(chunk_texts)
            self.vector_store.update_document(
                doc_id=target_id, new_chunks=chunk_texts, new_embeddings=embeddings
            )
            logger.info(f"Updated vector store for target: {target_id}")
        except IOError as e:
            logger.error(f"Error writing to target file {target_path}: {str(e)}")
            raise
