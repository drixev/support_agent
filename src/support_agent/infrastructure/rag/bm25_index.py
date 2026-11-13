import re

from rank_bm25 import BM25Okapi

from support_agent.domain.rag import Chunk, ScoredChunk

_TOKEN = re.compile(r"\w+") # \w incluye "_": ERR_QUOTA_EXCEEDED queda como un solo token


def tokenize(text:str) -> list[str]:
    return _TOKEN.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("BM25Index needs at least one chunk")
        
        self._chunks = chunks
        self._bm25 = BM25Okapi([tokenize(c.text) for c in chunks])
        
    def search(self, query: str, k: int) -> list[ScoredChunk]:
        scores = self._bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=scores.__getitem__,reverse=True)[:k]
        return [
            ScoredChunk(self._chunks[i], float(scores[i]), "bm25") 
            for i in top if scores[i] > 0
        ]
        