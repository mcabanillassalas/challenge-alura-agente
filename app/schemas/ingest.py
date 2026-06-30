from pydantic import BaseModel


class SavedFileItem(BaseModel):
    filename: str
    stored_as: str
    size_bytes: int


class IngestResponse(BaseModel):
    status: str
    saved_files: list[SavedFileItem]
    documents: int
    chunks: int
    raw_path: str
    processed_path: str