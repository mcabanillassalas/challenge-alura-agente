from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.ingest import IngestResponse, SavedFileItem
from app.services.document_loader import SUPPORTED_EXTENSIONS
from app.services.ingestion import rebuild_vector_index, save_uploaded_document

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    files: list[UploadFile] = File(...),
    embedding_provider: str = Form("ollama"),
    embedding_model: str = Form("nomic-embed-text"),
) -> IngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos")

    saved_files: list[SavedFileItem] = []

    try:
        for upload_file in files:
            filename = Path(upload_file.filename or "").name
            if not filename:
                raise ValueError("Uno de los archivos no tiene un nombre válido")

            if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Formato no soportado para {filename}. Solo se aceptan PDF, CSV o DOCX."
                )

            content = await upload_file.read()
            if not content:
                raise ValueError(f"El archivo {filename} está vacío")

            saved_path = save_uploaded_document(filename, content)
            saved_files.append(
                SavedFileItem(
                    filename=filename,
                    stored_as=str(saved_path),
                    size_bytes=len(content),
                )
            )

        summary = rebuild_vector_index(
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        return IngestResponse(
            status="ok",
            saved_files=saved_files,
            documents=summary["documents"],
            chunks=summary["chunks"],
            raw_path=summary["raw_path"],
            processed_path=summary["processed_path"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {exc}") from exc