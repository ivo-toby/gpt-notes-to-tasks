"""Service for semantic chunking of documents using LLM assistance."""

from typing import List, Dict, Any
import openai
import logging
import re
from datetime import datetime

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
        openai.api_key = config['api_key']
        self.client = openai.OpenAI()
        self.min_chunk_size = config.get('vector_store', {}).get('chunk_size_min', 50)
        self.max_chunk_size = config.get('vector_store', {}).get('chunk_size_max', 500)

    def chunk_document(self, content: str, doc_type: str = 'note') -> List[Dict[str, Any]]:
        """
        Split a document into semantic chunks using LLM assistance.

        Args:
            content: The document content to chunk
            doc_type: Type of document ('daily', 'weekly', 'meeting', 'learning', 'note')

        Returns:
            List of chunks with their metadata
        """
        # Extract frontmatter if present
        frontmatter, content = self._extract_frontmatter(content)
        
        # Extract title and tags from content
        title = self._extract_title(content)
        tags = self._extract_tags(content, frontmatter)
        
        # Choose appropriate chunking strategy based on document type
        if doc_type == 'daily':
            initial_chunks = self._split_daily_notes(content)
        elif doc_type in ['meeting', 'weekly']:
            initial_chunks = self._split_by_headers(content)
        elif doc_type == 'learning':
            initial_chunks = self._split_learning_notes(content)
        else:
            initial_chunks = self._split_by_semantic_markers(content)
        
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
                    processed_chunks.extend(
                        self._process_chunk_group('\\n'.join(current_chunk), 
                                               doc_type=doc_type,
                                               title=title,
                                               tags=tags,
                                               frontmatter=frontmatter)
                    )
                current_chunk = [chunk]
                current_size = chunk_size

        # Process any remaining chunks
        if current_chunk:
            processed_chunks.extend(
                self._process_chunk_group('\\n'.join(current_chunk),
                                       doc_type=doc_type,
                                       title=title,
                                       tags=tags,
                                       frontmatter=frontmatter)
            )

        return processed_chunks

    def _extract_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Extract YAML frontmatter from content if present.

        Args:
            content: Text content to process

        Returns:
            Tuple of (frontmatter dict, remaining content)
        """
        import yaml
        frontmatter = {}
        
        if content.startswith('---'):
            try:
                # Find the end of frontmatter
                end_index = content.find('---', 3)
                if end_index != -1:
                    frontmatter_yaml = content[3:end_index].strip()
                    frontmatter = yaml.safe_load(frontmatter_yaml) or {}
                    content = content[end_index + 3:].strip()
            except yaml.YAMLError:
                # If YAML parsing fails, assume no frontmatter
                pass
                
        return frontmatter, content

    def _extract_title(self, content: str) -> str:
        """
        Extract title from content.

        Args:
            content: Text content to process

        Returns:
            Extracted title or empty string
        """
        # Try to find first level 1 or 2 header
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        return ""

    def _extract_tags(self, content: str, frontmatter: Dict[str, Any]) -> List[str]:
        """
        Extract tags from content and frontmatter.

        Args:
            content: Text content to process
            frontmatter: Extracted frontmatter

        Returns:
            List of tags
        """
        tags = set()
        
        # Extract tags from frontmatter
        if 'tags' in frontmatter:
            if isinstance(frontmatter['tags'], list):
                tags.update(frontmatter['tags'])
            elif isinstance(frontmatter['tags'], str):
                tags.add(frontmatter['tags'])
        
        # Extract inline tags (#tag)
        tag_pattern = r'(?:^|\s)#([a-zA-Z][a-zA-Z0-9_-]*)'
        inline_tags = re.findall(tag_pattern, content)
        tags.update(inline_tags)
        
        return list(tags)

    def _split_daily_notes(self, content: str) -> List[str]:
        """
        Split daily notes by timestamp entries.

        Args:
            content: Text content to split

        Returns:
            List of chunks
        """
        chunks = []
        current_chunk = []
        
        for line in content.split('\n'):
            if re.match(r'\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+[AP]M\]', line):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            elif line.strip():
                current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return [c for c in chunks if len(c) >= self.min_chunk_size]

    def _split_by_headers(self, content: str) -> List[str]:
        """
        Split content by markdown headers.

        Args:
            content: Text content to split

        Returns:
            List of chunks
        """
        chunks = []
        current_chunk = []
        header_pattern = re.compile(r'^#{1,6}\s')
        
        for line in content.split('\n'):
            if header_pattern.match(line):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            elif line.strip():
                current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return [c for c in chunks if len(c) >= self.min_chunk_size]

    def _split_learning_notes(self, content: str) -> List[str]:
        """
        Split learning notes into individual entries.

        Args:
            content: Text content to split

        Returns:
            List of chunks
        """
        chunks = []
        current_chunk = []
        
        for line in content.split('\n'):
            if line.startswith('- ') or line.startswith('* '):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            elif line.strip() and current_chunk:
                current_chunk.append(line)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return [c for c in chunks if len(c) >= self.min_chunk_size]

    def _split_by_semantic_markers(self, content: str) -> List[str]:
        """
        Split content by various semantic markers.

        Args:
            content: Text content to split

        Returns:
            List of chunks
        """
        markers = [
            '\n## ', '\n### ', '\n#### ',  # Headers
            '\n- ', '\n* ',                 # List items
            '\n\n',                         # Paragraphs
            '\n[2'                          # Timestamps
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

    def _process_chunk_group(self, content: str, doc_type: str,
                           title: str = "", tags: List[str] = None,
                           frontmatter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
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
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": "You are a document processing assistant specializing in identifying semantically coherent chunks of text while preserving context and meaning."},
                    {"role": "user", "content": f"Split the following {doc_type} content into semantically coherent chunks between {self.min_chunk_size} and {self.max_chunk_size} characters. Identify a descriptive title for each chunk. Format as JSON: [{{\"content\": \"chunk text\", \"title\": \"chunk title\"}}].\n\nContent:\n{content}"}
                ]
            )
            
            # Parse the response
            import json
            chunks_data = json.loads(response.choices[0].message.content)
            
            # Add additional metadata
            for chunk in chunks_data:
                # Extract any dates from the chunk
                dates = self._extract_dates(chunk['content'])
                
                chunk['metadata'] = {
                    'title': chunk['title'],
                    'char_count': len(chunk['content']),
                    'semantic_chunk': True,
                    'doc_type': doc_type,
                    'doc_title': title,
                    'tags': tags or [],
                    'dates': dates
                }
                
                # Add relevant frontmatter fields
                if frontmatter:
                    for key, value in frontmatter.items():
                        if key not in ['content', 'title', 'tags']:  # Avoid conflicts
                            chunk['metadata'][f'frontmatter_{key}'] = value
            
            return chunks_data

        except Exception as e:
            logger.error(f"Error processing chunks with LLM: {str(e)}")
            # Fallback: Return simple chunk with basic metadata
            return [{
                'content': content,
                'metadata': {
                    'title': title or 'Unprocessed chunk',
                    'char_count': len(content),
                    'semantic_chunk': False,
                    'doc_type': doc_type,
                    'tags': tags or [],
                    'dates': self._extract_dates(content)
                }
            }]

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
            r'\[?(\d{4}-\d{2}-\d{2})\]?',  # YYYY-MM-DD
            r'\[?(\d{4}/\d{2}/\d{2})\]?',  # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    date_str = match.group(1)
                    # Normalize date format
                    date = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d')
                    dates.add(date.strftime('%Y-%m-%d'))
                except ValueError:
                    continue
                
        return list(dates)

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
                
                # Merge dates and tags
                current_dates = set(current_chunk['metadata'].get('dates', []))
                current_dates.update(chunk['metadata'].get('dates', []))
                current_chunk['metadata']['dates'] = list(current_dates)
                
                current_tags = set(current_chunk['metadata'].get('tags', []))
                current_tags.update(chunk['metadata'].get('tags', []))
                current_chunk['metadata']['tags'] = list(current_tags)
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
            
        return merged_chunks
