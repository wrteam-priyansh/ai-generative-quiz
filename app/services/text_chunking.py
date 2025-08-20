import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class TextChunkingService:
    """Service for intelligently chunking large text documents"""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation of tokens (approximately 1 token = 4 characters for English)"""
        return len(text) // 4
    
    @staticmethod
    def chunk_by_sentences(text: str, max_chunk_size: int = 2000) -> List[str]:
        """Chunk text by sentences to maintain context"""
        
        # Split by sentences (basic sentence detection)
        sentences = re.split(r'[.!?]+\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # If single sentence is too long, split it
                    chunks.extend(TextChunkingService._split_long_sentence(sentence, max_chunk_size))
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 50]  # Filter out very short chunks
    
    @staticmethod
    def chunk_by_paragraphs(text: str, max_chunk_size: int = 2000) -> List[str]:
        """Chunk text by paragraphs to maintain topic coherence"""
        
        # Split by paragraphs (double newlines or multiple spaces)
        paragraphs = re.split(r'\n\s*\n|\n{2,}', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # If single paragraph is too long, split by sentences
                    chunks.extend(TextChunkingService.chunk_by_sentences(paragraph, max_chunk_size))
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 50]
    
    @staticmethod
    def _split_long_sentence(sentence: str, max_size: int) -> List[str]:
        """Split a very long sentence into smaller parts"""
        
        # Try to split by commas first
        parts = sentence.split(', ')
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if len(current_chunk) + len(part) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = part
                else:
                    # If even a single part is too long, split by words
                    chunks.extend(TextChunkingService._split_by_words(part, max_size))
            else:
                current_chunk += ", " + part if current_chunk else part
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    def _split_by_words(text: str, max_size: int) -> List[str]:
        """Split text by words as a last resort"""
        
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = word
                else:
                    # If single word is too long, just truncate it
                    chunks.append(word[:max_size])
            else:
                current_chunk += " " + word if current_chunk else word
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    def smart_chunk_text(text: str, max_chunk_size: int = 2000, strategy: str = "paragraphs") -> List[str]:
        """
        Intelligently chunk text based on strategy
        
        Args:
            text: Input text to chunk
            max_chunk_size: Maximum characters per chunk
            strategy: 'paragraphs' or 'sentences'
        
        Returns:
            List of text chunks
        """
        
        # Clean the text
        text = text.strip()
        
        # If text is small enough, return as single chunk
        if len(text) <= max_chunk_size:
            return [text]
        
        logger.info(f"Chunking text of {len(text)} characters into chunks of max {max_chunk_size} characters")
        
        if strategy == "paragraphs":
            chunks = TextChunkingService.chunk_by_paragraphs(text, max_chunk_size)
        else:
            chunks = TextChunkingService.chunk_by_sentences(text, max_chunk_size)
        
        logger.info(f"Created {len(chunks)} chunks")
        
        return chunks
    
    @staticmethod
    def get_chunk_summary(chunks: List[str]) -> dict:
        """Get summary information about chunks"""
        
        total_chars = sum(len(chunk) for chunk in chunks)
        estimated_tokens = sum(TextChunkingService.estimate_tokens(chunk) for chunk in chunks)
        
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "estimated_total_tokens": estimated_tokens,
            "average_chunk_size": total_chars // len(chunks) if chunks else 0,
            "chunk_sizes": [len(chunk) for chunk in chunks]
        }