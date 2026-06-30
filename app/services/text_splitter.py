from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


def split_documents(documents: list):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_documents(documents)
