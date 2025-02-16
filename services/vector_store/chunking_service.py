"""Service for semantic chunking of documents using LLM assistance."""

from typing import List, Dict, Any
from openai import OpenAI
import logging

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
        self.client = OpenAI(api_key=config['api_key'])
        self.min_chunk_size = config.get('vector_store', {}).get('chunk_size_min', 50)
        self.max_chunk_size = config.get('vector_store', {}).get('chunk_size_max', 500)

    def chunk_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Split a document into semantic chunks using LLM assistance.

        Args:
            content: The document content to chunk

        Returns:
            List of chunks with their metadata
        """
        # First, split by obvious semantic boundaries
        initial_chunks = self._split_by_markers(content)
        
        # Process chunks to ensure size constraints and add metadata
        processed_chunks = []
        current_chunk = []
        current_size = 0

        for chunk in initial_chunks:
            chunk_size = len(chunk)
            
            if current_size + chunk_size <= self.max_chunk_size:
                current_chunk.append(chunk)
                current_size += chunk_size
            else:
                if current_chunk:
                    # Process the current chunk group
                    processed_chunks.extend(
                        self._process_chunk_group('\\n'.join(current_chunk))
                    )
                current_chunk = [chunk]
                current_size = chunk_size

        # Process any remaining chunks
        if current_chunk:
            processed_chunks.extend(
                self._process_chunk_group('\\n'.join(current_chunk))
            )

        return processed_chunks

    def _split_by_markers(self, content: str) -> List[str]:
        """
        Split content by common semantic markers.

        Args:
            content: Text content to split

        Returns:
            List of text chunks
        """
        # Initial split by headers, lists, etc.
        markers = [
            '\n## ', '\n### ', '\n#### ',  # Headers
            '\n- ', '\n* ',                 # List items
            '\n\n',                         # Paragraphs
            '\n[2'                          # Timestamps in format [2023-...
        ]
        
        chunks = [content]
        for marker in markers:
            new_chunks = []
            for chunk in chunks:
                # If marker is timestamp, handle differently
                if marker == '\n[2':
                    parts = chunk.split('\n[2')
                    new_chunks.extend(['[2' + p if i > 0 else p 
                                     for i, p in enumerate(parts) if p.strip()])
                else:
                    new_chunks.extend([c.strip() for c in chunk.split(marker) if c.strip()])
            chunks = new_chunks

        return [c for c in chunks if len(c) >= self.min_chunk_size]

    def _process_chunk_group(self, content: str) -> List[Dict[str, Any]]:
        """
        Process a group of chunks using LLM to ensure semantic coherence.

        Args:
            content: Content to process

        Returns:
            List of processed chunks with metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": "You are a document processing assistant. Your task is to identify semantically coherent chunks of text while preserving context and meaning."},
                    {"role": "user", "content": f"Split the following content into semantically coherent chunks between {self.min_chunk_size} and {self.max_chunk_size} characters. Identify a descriptive title for each chunk. Format as JSON: [{{\"content\": \"chunk text\", \"title\": \"chunk title\"}}].\n\nContent:\n{content}"}
                ]
            )
            
            # Parse the response
            import json
            chunks_data = json.loads(response.choices[0].message.content)
            
            # Add additional metadata
            for chunk in chunks_data:
                chunk['metadata'] = {
                    'title': chunk['title'],
                    'char_count': len(chunk['content']),
                    'semantic_chunk': True
                }
            
            return chunks_data

        except Exception as e:
            logger.error(f"Error processing chunks with LLM: {str(e)}")
            # Fallback: Return simple chunk with basic metadata
            return [{
                'content': content,
                'metadata': {
                    'title': 'Unprocessed chunk',
                    'char_count': len(content),
                    'semantic_chunk': False
                }
            }]

    def merge_small_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge chunks that are too small while maintaining semantic coherence.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            List of merged chunks
        """
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if not current_chunk:
                current_chunk = chunk
                continue
                
            if current_chunk['metadata']['char_count'] + len(chunk['content']) <= self.max_chunk_size:
                # Merge chunks
                current_chunk['content'] += f"\n{chunk['content']}"
                current_chunk['metadata']['char_count'] = len(current_chunk['content'])
                current_chunk['metadata']['title'] = f"{current_chunk['metadata']['title']} + {chunk['metadata']['title']}"
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
            
        return merged_chunks
