import os
import shutil
from pathlib import Path
from app.core.config import settings
from app.services.document_loader import load_documents_from_files
from app.services.text_splitter import split_documents
from app.services.vectorstore import build_vectorstore

def main():
    docs_path = Path(settings.docs_path)
    persist_dir = Path(settings.chroma_persist_directory)
    
    # 1. Limpieza inicial del vectorstore
    if persist_dir.exists():
        print(f"Limpiando base de datos anterior en {persist_dir}...")
        shutil.rmtree(persist_dir)
    
    # 2. Buscar todos los archivos PDF en la carpeta
    pdf_files = list(docs_path.glob("*.pdf"))
    print(f"Se encontraron {len(pdf_files)} manuales para procesar.")
    
    # 3. Procesar individualmente
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Procesando: {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f} MB)...")
        try:
            # Cargar un solo documento
            documents = load_documents_from_files([pdf_file])
            chunks = split_documents(documents)
            
            # Indexar e incorporar al vectorstore existente
            build_vectorstore(chunks)
            print(f"   -> ¡Completado! {len(chunks)} chunks agregados.")
        except Exception as e:
            print(f"   -> ERROR al procesar {pdf_file.name}: {str(e)}")

    print("\n¡Ingesta incremental completada con éxito!")

if __name__ == "__main__":
    main()
