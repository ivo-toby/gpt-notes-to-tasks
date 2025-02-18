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

    def update_obsidian_links(self, note_id: str, links: List[Dict[str, Any]]) -> None:
        """
        Update Obsidian-style wiki links in a note.

        Args:
            note_id: ID of the note to update
            links: List of links to add/update
        """
        # Get note content
        note_content = self.vector_store.get_note_content(note_id)
        if not note_content:
            return

        content = note_content["content"]

        # Add new wiki links
        for link in links:
            if link.get("add_wiki_link"):
                target = link["target_id"]
                alias = link.get("alias", target)
                content += f"\n[[{target}|{alias}]]"

        # Update the note in the vector store
        self.vector_store.update_document(doc_id=note_id, content=content)
