from app.core.config import settings
from app.services.ingestion import rebuild_vector_index


def main() -> None:
    print(f"Proveedor de embeddings: {settings.embedding_provider}")
    summary = rebuild_vector_index(settings.docs_path)
    print(
        "Ingesta completada. "
        f"Documentos: {summary['documents']} | Chunks: {summary['chunks']}"
    )


if __name__ == "__main__":
    main()
