from qdrant_client import AsyncQdrantClient

from support_agent.application.retrieval import HybridRetriever
from support_agent.config import Settings
from support_agent.infrastructure.rag.bm25_index import BM25Index
from support_agent.infrastructure.rag.embeddings import FastEmbedEmbedder
from support_agent.infrastructure.rag.qdrant_store import QdrantVectorStore


def build_store(settings: Settings) -> QdrantVectorStore:
    return QdrantVectorStore(AsyncQdrantClient(url=settings.qdrant_url), settings.qdrant_collection)


async def build_retriever(settings: Settings) -> HybridRetriever:
    embedder = FastEmbedEmbedder(settings.embedding_model)
    store = build_store(settings)
    
    return HybridRetriever(embedder, store, BM25Index(await store.all_chunks()))
    