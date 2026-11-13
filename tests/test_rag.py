from support_agent.application.retrieval import reciprocal_rank_fusion
from support_agent.domain.rag import Chunk, ScoredChunk
from support_agent.infrastructure.rag.chunking import chunk_markdown


def _sc(cid: str) -> ScoredChunk:
    return ScoredChunk(Chunk(cid, "d", cid), 0.0, "dense")


def test_rrf_rewards_agreement_between_rankings() -> None:
    fused = reciprocal_rank_fusion([[_sc("a"), _sc("b")], [_sc("b"), _sc("c")]])
    assert [s.chunk.id for s in fused][0] == "b"


def test_chunk_ids_are_deterministic() -> None:
    md = "# T\n" + "word " * 500
    assert [c.id for c in chunk_markdown("x.md", md)] == [c.id for c in chunk_markdown("x.md", md)]


def test_chunks_respect_overlap() -> None:
    chunks = chunk_markdown("x.md", " ".join(str(i) for i in range(300)), max_words=100, overlap=20)
    assert chunks[1].text.split()[0] == "80"