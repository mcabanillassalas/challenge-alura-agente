# Onboarding del proyecto: Exactus RAG Agent

## Contexto rápido

Este proyecto es un agente RAG en Python para consultar manuales del ERP Exactus.
La carpeta raíz de trabajo es `agente-alura-rag` y todo lo relevante del proyecto vive dentro de ella.

El objetivo del challenge es demostrar un flujo completo: cargar documentos, generar embeddings e índices, responder preguntas con IA y dejar evidencia de despliegue.

## Estado actual

- El RAG principal ya funciona.
- Los documentos fuente se guardan en `data/raw/exactus/`.
- Los embeddings e índices se generan en `data/processed/`.
- El frontend principal está en `frontend/streamlit_app.py`.
- La API principal está en FastAPI, en `app/main.py`.
- Ya existe soporte para cambiar proveedor y modelo tanto en el chat como en la carga.
- La carga de archivos permite PDF, CSV y DOCX.

## Estructura importante

- `app/`: backend FastAPI, esquemas y servicios.
- `frontend/`: interfaz Streamlit.
- `scripts/`: comandos de ingesta y reconstrucción de índice.
- `data/raw/exactus/`: documentos originales subidos.
- `data/processed/`: vectorstore persistido y salida procesada.
- `challenge/`: requerimientos, entregables y guía del challenge.
- `tests/`: pruebas automáticas mínimas.

## Flujo funcional

1. El usuario sube archivos PDF, CSV o DOCX desde el frontend.
2. Los archivos se guardan en `data/raw/exactus/`.
3. Se limpian y se transforman en documentos para RAG.
4. Se generan chunks y embeddings.
5. El índice se persiste en `data/processed/`.
6. El chat consulta la API y responde usando el contexto recuperado.

## Proveedores e IA

### Chat

El chat permite elegir proveedor y modelo por consulta.
Soporta:

- Ollama
- Gemini
- OpenAI

### Carga / embeddings

La sección de carga tiene su propio selector de proveedor y modelo.
Ese selector existe para que la carga se haga normalmente antes de producción y, solo si es necesario, también en producción.

Por defecto, la carga usa Ollama.

## Variables de entorno relevantes

- `LLM_PROVIDER`: proveedor por defecto del chat.
- `EMBEDDING_PROVIDER`: proveedor por defecto de embeddings.
- `OLLAMA_LLM_MODEL`: modelo Ollama para chat.
- `OLLAMA_EMBEDDING_MODEL`: modelo Ollama para embeddings.
- `OPENAI_API_KEY`: clave de OpenAI.
- `OPENAI_CHAT_MODEL`: modelo de chat de OpenAI.
- `OPENAI_EMBEDDING_MODEL`: modelo de embeddings de OpenAI.
- `GEMINI_API_KEY`: clave de Gemini.
- `GEMINI_CHAT_MODEL`: modelo Gemini para chat.
- `CHROMA_PERSIST_DIRECTORY`: ruta del vectorstore procesado, normalmente `data/processed`.
- `DOCS_PATH`: ruta de entrada de documentos, normalmente `data/raw/exactus`.
- `TOP_K`: número de fragmentos recuperados por consulta.
- `CHUNK_SIZE`: tamaño de chunk para el splitter.
- `CHUNK_OVERLAP`: solapamiento entre chunks.

## Cómo ejecutar localmente

```powershell
cd D:\DevALURA\challenge-alura-agente\agente-alura-rag
.\env3.11\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
streamlit run frontend/streamlit_app.py
```

## Ingesta y reconstrucción de índice

La ingesta actual se hace por la API del frontend o por script.

Script manual:

```powershell
python -m scripts.ingest
```

Si necesitas reconstruir desde cero el índice y volver a procesar los documentos, usa el script de rebuild.

## Endpoints útiles

- `GET /health`: estado de la API.
- `POST /api/v1/ask`: responde preguntas sobre los manuales.
- `POST /api/v1/ingest`: recibe archivos y vuelve a generar el índice.

## Reglas de trabajo

- No tocar archivos fuera de `agente-alura-rag`.
- Mantener el `.gitignore` actualizado para no versionar el entorno virtual ni artefactos locales.
- No sobrescribir `data/processed/` manualmente salvo cuando se quiera reconstruir el índice.
- Antes de cambiar el flujo RAG, validar que `tests/test_health.py` siga pasando.

## Siguientes mejoras previstas

- Afinar la UI para mostrar métricas de carga e indexación.
- Mejorar manejo de errores en la carga de archivos.
- Agregar más pruebas para ingesta, embeddings y respuesta del chat.
- Mantener documentación sincronizada con el comportamiento real del código.
