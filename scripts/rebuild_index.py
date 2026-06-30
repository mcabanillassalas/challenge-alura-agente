import shutil
from pathlib import Path

from app.core.config import settings
from scripts.ingest import main as ingest_main


def main() -> None:
    vectorstore_path = Path(settings.chroma_persist_directory)
    if vectorstore_path.exists():
        shutil.rmtree(vectorstore_path)
        print(f"Vectorstore eliminado: {vectorstore_path}")
    ingest_main()


if __name__ == "__main__":
    main()
