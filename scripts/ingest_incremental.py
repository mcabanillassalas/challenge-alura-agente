import os
import shutil
import time
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
            print(f"   -> Dividido en {len(chunks)} chunks.")
            
            # Indexar en sub-lotes pequeños para respetar el límite de cuota (100 RPM)
            # 20 chunks por lote con 3s de espera = ~15 a 20 peticiones por minuto (muy seguro)
            sub_batch_size = 20
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
                        # Pausa de 3 segundos entre lotes para mantenernos bajo el límite de RPM
                        time.sleep(3)
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "Quota exceeded" in err_str:
                            retries -= 1
                            # Limitar el tiempo máximo de espera a 60s para evitar que SSH se desconecte por inactividad
                            actual_wait = min(wait_time, 60)
                            print(f"   -> [429 Quota Exceeded] Esperando {actual_wait}s para reintentar ({retries} reintentos restantes)...")
                            time.sleep(actual_wait)
                            wait_time *= 2  # Backoff exponencial para el siguiente intento
                        else:
                            raise e
                
                if not success:
                    raise Exception(f"No se pudo indexar el lote de chunks a partir del índice {j} tras varios reintentos.")
            
            print(f"   -> ¡Completado! {len(chunks)} chunks agregados.")
        except Exception as e:
            print(f"   -> ERROR al procesar {pdf_file.name}: {str(e)}")

    print("\n¡Ingesta incremental completada con éxito!")

if __name__ == "__main__":
    main()

