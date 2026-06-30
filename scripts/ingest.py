from app.core.config import settings
from app.services.document_loader import load_pdf_documents
from app.services.text_splitter import split_documents
from app.services.vectorstore import build_vectorstore


def main() -> None:
    print(f"Proveedor de embeddings: {settings.embedding_provider}")
    documents = load_pdf_documents(settings.docs_path)
    chunks = split_documents(documents)
    build_vectorstore(chunks)
    print(f"Ingesta completada. Documentos: {len(documents)} | Chunks: {len(chunks)}")


if __name__ == "__main__":
    main()
