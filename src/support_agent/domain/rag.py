from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    doc_id:str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)
    

@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float
    source: Literal["dense","bm25","hybrid"]
    
