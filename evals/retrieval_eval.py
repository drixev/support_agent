import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

from support_agent.composition import build_retriever
from support_agent.config import get_settings
from support_agent.domain.rag import ScoredChunk

SearchFn = Callable[[str, int], Awaitable[list[ScoredChunk]]]


async def evaluate(name: str, search: SearchFn, golden: list[dict], k: int = 3) -> None:
    hit1 = hitk = 0
    rr = 0.0
    for case in golden:
        doc_ids = [r.chunk.doc_id for r in await search(case["query"], k)]
        ranks = [i for i, d in enumerate(doc_ids, start=1) if d in case["relevant"]]
        if ranks:
            hitk += 1
            hit1 += ranks[0] == 1
            rr += 1 / ranks[0]
    n = len(golden)
    print(f"{name:<7} hit@1={hit1/n:.2f}  hit@{k}={hitk/n:.2f}  MRR={rr/n:.2f}")


def load_golden(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


async def main() -> None:
    golden = await asyncio.to_thread(load_golden, Path("evals/golden_retrieval.jsonl"))
    retriever = await build_retriever(get_settings())
    await evaluate("dense", retriever.dense, golden)
    await evaluate("bm25", retriever.lexical, golden)
    await evaluate("hybrid", retriever.retrieve, golden)


if __name__ == "__main__":
    asyncio.run(main())