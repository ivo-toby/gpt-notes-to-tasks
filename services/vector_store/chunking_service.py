"""Service for semantic chunking of documents using LLM assistance."""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

import openai

logger = logging.getLogger(__name__)


class ChunkingService:
    """Manages the semantic chunking of documents."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the chunking service.

        Args:
            config: Configuration dictionary containing API settings
        """
        self.config = config
        openai.api_key = config["api_key"]
        self.client = openai.OpenAI()
        self.min_chunk_size = config.get("vector_store", {}).get("chunk_size_min", 50)
        self.max_chunk_size = config.get("vector_store", {}).get("chunk_size_max", 500)

class ParagraphChunkingService:
    """Manages paragraph-based chunking of documents."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the paragraph chunking service.

        Args:
            config: Configuration dictionary containing chunking settings
        """
        self.config = config
        self.max_length = config.get("paragraph_chunking", {}).get("max_length", 500)
        self.overlap = config.get("paragraph_chunking", {}).get("overlap", 50)

    @staticmethod
    def create(config: Dict[str, Any]) -> 'ChunkingService':
        """
        Factory method to create a chunking service based on configuration.

        Args:
            config: Configuration dictionary

        Returns:
            An instance of a chunking service
        """
        strategy = config.get("chunking_strategy", "semantic")
        if strategy == "paragraph":
            return ParagraphChunkingService(config)
        return ChunkingService(config)

    def chunk_document(self, content: str, doc_type: str = "note") -> List[Dict[str, Any]]:
        """
        Chunk a document into paragraphs with overlap.

        Args:
            content: Content to chunk
            doc_type: Type of document

        Returns:
            List of chunks with metadata
        """
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = []

        for paragraph in paragraphs:
            if len(" ".join(current_chunk + [paragraph])) <= self.max_length:
                current_chunk.append(paragraph)
            else:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = current_chunk[-self.overlap:] + [paragraph]

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return [{"content": chunk, "metadata": {"doc_type": doc_type}} for chunk in chunks]
    """Manages the semantic chunking of documents."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the chunking service.

        Args:
            config: Configuration dictionary containing API settings
        """
        self.config = config
        openai.api_key = config["api_key"]
        self.client = openai.OpenAI()
        self.min_chunk_size = config.get("vector_store", {}).get("chunk_size_min", 50)
        self.max_chunk_size = config.get("vector_store", {}).get("chunk_size_max", 500)

    def _process_chunk_group(
        self,
        content: str,
        doc_type: str = "note",
        title: str = "",
        tags: List[str] = None,
        frontmatter: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a group of chunks using LLM to ensure semantic coherence.

        Args:
            content: Content to process
            doc_type: Type of document
            title: Document title
            tags: Document tags
            frontmatter: Document frontmatter

        Returns:
            List of processed chunks with metadata
        """
        try:
            # Create a more explicit prompt
            system_prompt = """You are a document processing assistant. Your task is to:
1. Split the provided content into semantically coherent chunks
2. Each chunk should be between the specified minimum and maximum character lengths
3. Provide a descriptive title for each chunk
4. Return the results in valid JSON format: [{"content": "chunk text", "title": "chunk title"}]

Important:
- Preserve the original content exactly within each chunk
- Ensure each chunk is semantically complete (don't split mid-sentence)
- Make titles descriptive but concise
- Always return valid JSON array of objects"""

            user_prompt = f"""Split the following {doc_type} content into semantically coherent chunks between {self.min_chunk_size} and {self.max_chunk_size} characters.

Content to process:
{content}

Return only the JSON array with no additional text."""

            response = self.client.chat.completions.create(
                model=self.config["chunking_model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                response_format={"type": "json_object"},  # Request JSON response
            )

            # Log the raw response for debugging
            logger.debug(f"Raw LLM response: {response.choices[0].message.content}")

            # Parse the response
            try:
                response_content = response.choices[0].message.content.strip()
                if not response_content:
                    raise ValueError("Empty response from LLM")

                chunks_data = []
                try:
                    # Try to parse as a JSON object with a 'chunks' key
                    parsed = json.loads(response_content)
                    if isinstance(parsed, dict) and "chunks" in parsed:
                        chunks_data = parsed["chunks"]
                    else:
                        # Try parsing as direct array
                        chunks_data = parsed if isinstance(parsed, list) else [parsed]
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a single chunk
                    logger.warning(
                        f"Failed to parse LLM response as JSON: {response_content[:100]}..."
                    )
                    raise

                # Validate the structure of each chunk
                valid_chunks = []
                for chunk in chunks_data:
                    if (
                        isinstance(chunk, dict)
                        and "content" in chunk
                        and "title" in chunk
                    ):
                        chunk_content = chunk["content"]
                        if (
                            self.min_chunk_size
                            <= len(chunk_content)
                            <= self.max_chunk_size
                        ):
                            valid_chunks.append(chunk)
                        else:
                            logger.warning(
                                f"Chunk size {len(chunk_content)} outside bounds for title: {chunk['title']}"
                            )

                if not valid_chunks:
                    raise ValueError("No valid chunks found in LLM response")

                # Add metadata to valid chunks
                for chunk in valid_chunks:
                    # Extract any dates from the chunk
                    dates = self._extract_dates(chunk["content"])

                    chunk["metadata"] = {
                        "title": chunk["title"],
                        "char_count": len(chunk["content"]),
                        "semantic_chunk": True,
                        "doc_type": doc_type,
                        "doc_title": title,
                        "tags": tags or [],
                        "dates": dates,
                    }

                    # Add relevant frontmatter fields
                    if frontmatter:
                        for key, value in frontmatter.items():
                            if key not in ["content", "title", "tags"]:
                                chunk["metadata"][f"frontmatter_{key}"] = value

                return valid_chunks

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error processing LLM response: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Error processing chunks with LLM: {str(e)}")
            # Fallback: create a single chunk with basic metadata
            return [
                {
                    "content": content,
                    "metadata": {
                        "title": title or "Unprocessed chunk",
                        "char_count": len(content),
                        "semantic_chunk": False,
                        "doc_type": doc_type,
                        "tags": tags or [],
                        "dates": self._extract_dates(content),
                    },
                }
            ]

    def _extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text content.

        Args:
            text: Text to extract dates from

        Returns:
            List of date strings in YYYY-MM-DD format
        """
        dates = set()

        # Match common date formats
        patterns = [
            r"\[?(\d{4}-\d{2}-\d{2})\]?",  # YYYY-MM-DD
            r"\[?(\d{4}/\d{2}/\d{2})\]?",  # YYYY/MM/DD
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    date_str = match.group(1)
                    # Normalize date format
                    date = datetime.strptime(date_str.replace("/", "-"), "%Y-%m-%d")
                    dates.add(date.strftime("%Y-%m-%d"))
                except ValueError:
                    continue

        return list(dates)

    def chunk_document(
        self, content: str, doc_type: str = "note"
    ) -> List[Dict[str, Any]]:
        """
        Chunk a document into semantically coherent parts.

        Args:
            content: Content to chunk
            doc_type: Type of document

        Returns:
            List of chunks with metadata
        """
        return self._process_chunk_group(content, doc_type=doc_type)
