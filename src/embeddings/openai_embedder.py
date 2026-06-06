"""OpenAI Embedding wrapper with batching and retry"""
import asyncio
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np

class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-large", batch_size: int = 100):
        self.client = AsyncOpenAI()
        self.model = model
        self.batch_size = batch_size

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            response = await self.client.embeddings.create(model=self.model, input=batch)
            all_embeddings.extend([e.embedding for e in response.data])
        return all_embeddings

    async def embed_single(self, text: str) -> list[float]:
        result = await self.embed_batch([text])
        return result[0]

    @property
    def dimension(self) -> int:
        return 3072 if "3-large" in self.model else 1536
