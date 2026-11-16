import asyncio
import httpx
from openai import AsyncOpenAI
from .config import settings

class Provider:
    def __init__(self):
        self.http = httpx.AsyncClient(base_url=settings.api_base_url + '/', headers={'Authorization':f'Bearer {settings.siliconflow_api_key}'}, timeout=90)
        self.llm = AsyncOpenAI(api_key=settings.siliconflow_api_key or 'missing', base_url=settings.api_base_url)
        self.limit = asyncio.Semaphore(4)
    async def close(self):
        await self.http.aclose()
        await self.llm.close()
    async def post(self, endpoint, payload):
        async with self.limit:
            for attempt in range(4):
                response = await self.http.post(endpoint, json=payload)
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                return response.json()
    async def embed(self, texts):
        async def batch(values):
            result = await self.post('embeddings', {'model':settings.embedding_model,'input':values})
            vectors = [d['embedding'] for d in sorted(result['data'], key=lambda d:d['index'])]
            if len(vectors) != len(values) or any(len(v) != 1024 for v in vectors):
                raise ValueError('Embedding response must contain one 1024-dimensional vector per input')
            return vectors
        groups = await asyncio.gather(*(batch(texts[i:i+16]) for i in range(0,len(texts),16)))
        return [v for group in groups for v in group]
    async def rerank(self, query, rows):
        if not rows:
            return []
        result = await self.post('rerank', {'model':settings.rerank_model,'query':query,'documents':[r['text'] for r in rows], 'top_n':5, 'return_documents':False})
        return [dict(rows[r['index']], score=r['relevance_score']) for r in result['results']]
