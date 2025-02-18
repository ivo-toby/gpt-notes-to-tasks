"""Service for generating embeddings using OpenAI's API."""

import logging
from typing import Any, Dict, List

import openai
from tqdm import tqdm

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages the generation of embeddings for text content."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the embedding service.

        Args:
            config: Configuration dictionary containing API settings
        """
        self.config = config
        openai.api_key = config["api_key"]
        self.client = openai.OpenAI()
        # self.model = "text-embedding-3-small"  # Current best model for embeddings
        self.model = "text-embedding-ada-002"  # Current best model for embeddings
        self.batch_size = 100  # Maximum batch size for embedding requests

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single piece of text.

        Args:
            text: Text to generate embedding for

        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(model=self.model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def embed_chunks(
        self, chunks: List[str], show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple text chunks.

        Args:
            chunks: List of text chunks to generate embeddings for
            show_progress: Whether to show a progress bar

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches
        for i in tqdm(
            range(0, len(chunks), self.batch_size),
            disable=not show_progress,
            desc="Generating embeddings",
        ):
            batch = chunks[i : i + self.batch_size]
            try:
                response = self.client.embeddings.create(model=self.model, input=batch)
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {str(e)}")
                raise

        return embeddings

    def get_embedding_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the current embedding configuration.

        Returns:
            Dictionary containing embedding metadata
        """
        return {
            "model": self.model,
            "dimensions": 1536,  # Ada-002 embedding size
            "normalized": True,
        }
