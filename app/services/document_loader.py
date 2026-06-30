from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


def load_pdf_documents(docs_path: str) -> list:
    base_path = Path(docs_path)
    if not base_path.exists():
        raise FileNotFoundError(f"La ruta de documentos no existe: {docs_path}")

    pdf_files = list(base_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No se encontraron archivos PDF en: {docs_path}")

    documents = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(str(pdf_file))
        pages = loader.load()
        for page in pages:
            page.metadata["source"] = pdf_file.name
        documents.extend(pages)

    return documents
