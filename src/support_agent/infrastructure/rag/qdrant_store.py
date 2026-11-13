from qdrant_client import AsyncQdrantClient, models

from support_agent.domain.rag import Chunk, ScoredChunk


def _to_chunk(point:models.Record | models.ScoredPoint) -> Chunk:
    payload = dict(point.payload or {})
    return Chunk(str(point.id), payload.pop("doc_id"), payload.pop("text"), payload)


class QdrantVectorStore:
    def __init__(self, client: AsyncQdrantClient, collection:str) -> None:
        self._client = client
        self._collection = collection
        
    async def ensure_collection(self, dim:int) -> None:
        if not await self._client.collection_exists(self._collection):
            await self._client.create_collection(
                self._collection,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
            )
            

    async def upsert(self, chunks:list[Chunk], vectors: list[list[float]]) -> None:
        points = [
            models.PointStruct(
                id=c.id, vector=v, payload={"doc_id": c.doc_id, "text": c.text, **c.metadata}
            )
            for c, v in zip(chunks, vectors, strict=True)
        ]
        
        await self._client.upsert(self._collection, points=points, wait=True)
        
    
    async def search(self, vector: list[float], k: int) -> list[ScoredChunk]:
        res = await self._client.query_points(
            self._collection, query=vector, limit=k, with_payload=True
        )
        
        return [ScoredChunk(_to_chunk(p), p.score, "dense") for p in res.points]
    
    async def all_chunks(self) -> list[Chunk]:
        """Qdrant es la fuente de verdad; BM25 se reconstruye desde aqui al arrancar"""
        chunks: list[Chunk] = []
        offset = None
        while True:
            points, offset = await self._client.scroll(
                self._collection, limit=256, offset=offset, with_payload=True, with_vectors=False
            )
            chunks.extend(_to_chunk(p) for p in points)
            if offset is None:
                return chunks