"""Semantic Chunking Strategy"""
import re
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 64, model: str = "all-MiniLM-L6-v2"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.model = SentenceTransformer(model)

    def chunk(self, text: str) -> list[str]:
        sentences = self._split_sentences(text)
        if not sentences:
            return []
        embeddings = self.model.encode(sentences, batch_size=64)
        chunks, current_chunk = [], []
        current_len = 0
        for i, (sent, emb) in enumerate(zip(sentences, embeddings)):
            if current_len + len(sent) > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep overlap sentences
                overlap_sents = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sents[:]
                current_len = sum(len(s) for s in current_chunk)
            current_chunk.append(sent)
            current_len += len(sent)
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
