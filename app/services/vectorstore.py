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


def build_vectorstore(
    chunks: list,
    provider_override: str | None = None,
    model_override: str | None = None,
    base_url_override: str | None = None,
) -> Chroma:
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings_model(
            provider_override=provider_override,
            model_override=model_override,
            base_url_override=base_url_override,
        ),
        persist_directory=settings.chroma_persist_directory
    )
    return vectorstore
