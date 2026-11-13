import asyncio

from fastembed import TextEmbedding


class FastEmbedEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model = TextEmbedding(model_name=model_name)
        self._dim = len(next(iter(self._model.embed(["probe"]))))
        
    @property
    def dim(self) -> int:
        return self._dim
    
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(
            lambda:[v.tolist() for v in self._model.passage_embed(texts)]
        )
        
    async def embed_query(self, query: str) -> list[float]:
        vectors = await asyncio.to_thread(
            lambda: [v.tolist() for v in self._model.query_embed(query)]
        )
        
        return vectors[0]
    
    
    