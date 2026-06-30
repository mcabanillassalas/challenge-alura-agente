from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import settings
from app.services.document_loader import load_documents_from_files, load_documents_from_path
from app.services.text_splitter import split_documents
from app.services.vectorstore import build_vectorstore


def save_uploaded_document(filename: str, content: bytes) -> Path:
    raw_path = Path(settings.docs_path)
    raw_path.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    destination = raw_path / safe_name
    destination.write_bytes(content)
    return destination


def index_documents(
    documents: list,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> int:
    chunks = split_documents(documents)
    build_vectorstore(
        chunks,
        provider_override=embedding_provider,
        model_override=embedding_model,
        base_url_override=embedding_base_url,
    )
    return len(chunks)


def index_uploaded_files(
    file_paths: list[Path],
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict[str, int | str]:
    documents = load_documents_from_files(file_paths)
    chunks = index_documents(
        documents,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        embedding_base_url=embedding_base_url,
    )

    return {
        "documents": len(documents),
        "chunks": chunks,
        "raw_path": str(Path(settings.docs_path)),
        "processed_path": str(Path(settings.chroma_persist_directory)),
    }


def rebuild_vector_index(
    source_path: str | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict[str, int | str]:
    docs_path = Path(source_path or settings.docs_path)
    docs_path.mkdir(parents=True, exist_ok=True)

    persist_dir = Path(settings.chroma_persist_directory)
    if persist_dir.exists():
        shutil.rmtree(persist_dir)

    documents = load_documents_from_path(str(docs_path))
    chunks = index_documents(
        documents,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        embedding_base_url=embedding_base_url,
    )

    return {
        "documents": len(documents),
        "chunks": chunks,
        "raw_path": str(docs_path),
        "processed_path": str(persist_dir),
    }