import sys
import os
import time
from pathlib import Path
from app.core.config import settings
from app.services.document_loader import load_documents_from_files
from app.services.text_splitter import split_documents
from app.services.vectorstore import build_vectorstore

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.ingest_pdf_incremental <nombre_del_archivo.pdf>")
        sys.exit(1)
        
    pdf_filename = sys.argv[1]
    docs_path = Path(settings.docs_path)
    pdf_file = docs_path / pdf_filename
    
    # Validar si existe en la ruta de documentos o de forma directa
    if not pdf_file.exists():
        pdf_file = Path(pdf_filename)
        if not pdf_file.exists():
            print(f"ERROR: No se encontró el archivo '{pdf_filename}' ni en '{settings.docs_path}' ni en la ruta actual.")
            sys.exit(1)
            
    print(f"\nProcesando archivo individual: {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f} MB)...")
    try:
        # Cargar el documento
        documents = load_documents_from_files([pdf_file])
        chunks = split_documents(documents)
        print(f"   -> Dividido en {len(chunks)} chunks.")
        
        # Indexar en sub-lotes pequeños para respetar el límite de cuota (100 RPM)
        sub_batch_size = 100
        for j in range(0, len(chunks), sub_batch_size):
            sub_batch = chunks[j : j + sub_batch_size]
            success = False
            retries = 5
            wait_time = 20
            
            while not success and retries > 0:
                try:
                    print(f"   -> Indexando chunks {j} a {min(j + sub_batch_size, len(chunks))}...")
                    build_vectorstore(sub_batch)
                    success = True
                    # Pausa corta entre lotes
                    time.sleep(2)
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "Quota exceeded" in err_str:
                        retries -= 1
                        print(f"   -> [429 Quota Exceeded] Esperando {wait_time}s para reintentar ({retries} reintentos restantes)...")
                        time.sleep(wait_time)
                        wait_time *= 2  # Backoff exponencial
                    else:
                        raise e
            
            if not success:
                raise Exception(f"No se pudo indexar el lote de chunks a partir del índice {j} tras varios reintentos.")
        
        print(f"   -> ¡Completado con éxito! {len(chunks)} chunks agregados al vectorstore.")
    except Exception as e:
        print(f"   -> ERROR al procesar {pdf_file.name}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
