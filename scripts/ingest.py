import asyncio
import sys
from pathlib import Path

from support_agent.composition import build_store
from support_agent.config import get_settings
from support_agent.infrastructure.rag.chunking import chunk_markdown
from support_agent.infrastructure.rag.embeddings import FastEmbedEmbedder


def load_chunks(docs_dir: Path) -> list:
    return [
        c
        for p in sorted(docs_dir.rglob("*.md"))
        for c in chunk_markdown(p.relative_to(docs_dir).as_posix(), p.read_text("utf-8"))
    ]


async def main(docs_dir: Path) -> None:
    settings = get_settings()
    embedder = FastEmbedEmbedder(settings.embedding_model)
    store = build_store(settings)
    await store.ensure_collection(embedder.dim)
    chunks = await asyncio.to_thread(load_chunks, docs_dir)

    await store.upsert(chunks, await embedder.embed_documents([c.text for c in chunks]))
    print(f"Ingested {len(chunks)} chunks from {docs_dir}")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs")))
    