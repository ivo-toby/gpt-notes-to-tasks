"""Service for managing and analyzing links between notes."""

import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LinkService:
    """Manages link relationships and suggestions between notes."""

    def __init__(self, vector_store):
        """
        Initialize the link service.

        Args:
            vector_store: Instance of VectorStoreService for content queries
        """
        self.vector_store = vector_store

    def analyze_relationships(self, note_id: str) -> Dict[str, Any]:
        """
        Analyze relationships for a specific note.

        Args:
            note_id: ID of the note to analyze

        Returns:
            Dictionary containing relationship analysis
        """
        # Strip the base path if it exists
        base_path = "~/workspace/rd/cf-notes/"
        expanded_base = os.path.expanduser(base_path)
        if note_id.startswith(expanded_base):
            note_id = note_id[len(expanded_base) :]
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
            if result_id and result_id not in existing and result_id != note_id:
                suggestions.append(
                    {
                        "note_id": result_id,
                        "similarity": result["similarity"],
                        "reason": "Content similarity",
                        "preview": result["content"][:200],
                    }
                )

        return suggestions

    def update_obsidian_links(self, note_id: str, links: List[Dict[str, Any]], 
                             update_backlinks: bool = True) -> None:
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
                        self._update_target_backlinks(target, note_id)

            elif link.get("remove_wiki_link"):
                # Remove existing link
                content = self._remove_wiki_link(content, link["target_id"])
                updated = True

        if updated:
            # Update the note content
            chunks = self._rechunk_content(content)
            embeddings = self._generate_embeddings(chunks)
            self.vector_store.update_document(
                doc_id=note_id,
                new_chunks=chunks,
                new_embeddings=embeddings
            )
            logger.info(f"Updated links in note: {note_id}")

    def _generate_alias(self, target: str) -> str:
        """Generate a readable alias from the target ID."""
        # Remove file extension and path
        alias = os.path.basename(target).replace('.md', '')
        # Convert kebab/snake case to title case
        alias = ' '.join(word.capitalize() for word in re.split(r'[-_]', alias))
        return alias

    def _has_wiki_link(self, content: str, target: str) -> bool:
        """Check if content already contains a wiki link to target."""
        pattern = rf"\[\[{re.escape(target)}(?:\|[^\]]+)?\]\]"
        return bool(re.search(pattern, content))

    def _insert_wiki_link(self, content: str, new_link: str) -> str:
        """Insert a wiki link in a semantically appropriate location."""
        # Try to find a "Related" or "Links" section
        sections = ["## Related", "## Links", "## References"]
        for section in sections:
            if section in content:
                # Insert after section header
                parts = content.split(section, 1)
                return f"{parts[0]}{section}\n{new_link}\n{parts[1]}"
        
        # If no appropriate section found, add to end with header
        return f"{content.rstrip()}\n\n## Related\n{new_link}\n"

    def _remove_wiki_link(self, content: str, target: str) -> str:
        """Remove a wiki link from the content."""
        pattern = rf"\[\[{re.escape(target)}(?:\|[^\]]+)?\]\]\n?"
        return re.sub(pattern, '', content)

    def _update_target_backlinks(self, target_id: str, source_id: str) -> None:
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
                content = content.replace("## Backlinks\n", f"## Backlinks\n{backlink}\n")

        # Update target note
        chunks = self._rechunk_content(content)
        embeddings = self._generate_embeddings(chunks)
        self.vector_store.update_document(
            doc_id=target_id,
            new_chunks=chunks,
            new_embeddings=embeddings
        )
