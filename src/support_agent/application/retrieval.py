import asyncio
from collections import defaultdict

from support_agent.domain.ports import Embedder, KeywordIndex, VectorStore
from support_agent.domain.rag import Chunk, ScoredChunk


def reciprocal_rank_fusion(
    rankings: list[list[ScoredChunk]], k:int = 60
) -> list[ScoredChunk]:
    scores: dict[str, float] = defaultdict(float)
    by_id: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item.chunk.id] += 1.0 / (k + rank)
            by_id[item.chunk.id] = item.chunk
            
    ordered = sorted(scores, key=scores.__getitem__, reverse=True)
    return [ScoredChunk(by_id[cid], scores[cid], "hybrid") for cid in ordered]

class HybridRetriever:
    def __init__(
        self, embedder: Embedder, store: VectorStore, keyword:KeywordIndex, candidates: int = 20
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._keyword = keyword
        self._candidates = candidates
        
    async def dense(self, query: str, k: int) -> list[ScoredChunk]:
        return await self._store.search(await self._embedder.embed_query(query), k)
    
    async def lexical(self, query:str, k: int) -> list[ScoredChunk]:
        return await asyncio.to_thread(self._keyword.search, query, k)
    
    async def retrieve(self, query:str, k:int) -> list[ScoredChunk]:
        async with asyncio.TaskGroup() as tg:
            dense_t = tg.create_task(self.dense(query, self._candidates))
            lexical_t = tg.create_task(self.lexical(query, self._candidates))
        
        return reciprocal_rank_fusion([dense_t.result(), lexical_t.result()])[:k]