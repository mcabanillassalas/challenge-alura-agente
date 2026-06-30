from pathlib import Path

from langchain_chroma import Chroma

from app.core.config import settings
from app.services.embeddings import get_embeddings_model


def get_vectorstore() -> Chroma:
    persist_dir = Path(settings.chroma_persist_directory)
    if not persist_dir.exists():
        raise FileNotFoundError(
            f"No existe el vectorstore en '{settings.chroma_persist_directory}'. Ejecuta primero python -m scripts.ingest"
        )

    return Chroma(
        persist_directory=settings.chroma_persist_directory,
        embedding_function=get_embeddings_model()
    )


def build_vectorstore(chunks: list) -> Chroma:
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings_model(),
        persist_directory=settings.chroma_persist_directory
    )
    return vectorstore
