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
- La carga por frontend indexa solo los archivos recién subidos; la reconstrucción completa queda para `python -m scripts.rebuild_index`.
- Debajo de la carga de documentos existe una acción de reindexación que usa el mismo proveedor y modelo seleccionados para la carga.
- La ingesta agrega metadatos del manual (`manual_code`, `manual_family`, `document_title`) y la recuperación prioriza el manual correcto según el tema de la consulta.
- El mapeo temático editable vive en `app/core/manual_routing.py`.
- El mapeo temático editable se guarda en `app/core/manual_routing.yml`.

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

Gemini requiere `langchain-google-genai==2.1.12` en el entorno del proyecto para mantener compatibilidad con el stack de LangChain usado aquí.

### Carga / embeddings

La sección de carga tiene su propio selector de proveedor y modelo.
Ese selector existe para que la carga se haga normalmente antes de producción y, solo si es necesario, también en producción.

Por defecto, la carga usa Ollama.

La recuperación también usa metadatos del documento para priorizar el manual correcto cuando la consulta apunta a un tema específico, por ejemplo usuarios, nómina o facturación.

Si necesitas agregar nuevas referencias, edita `app/core/manual_routing.py` y añade el código del manual con sus palabras clave.

Si prefieres mantener las reglas fuera del código, edita `app/core/manual_routing.yml`.

Como punto de partida, puedes añadir sinónimos de negocio como "alta de usuarios", "asignar permisos", "kardex" o "conciliación bancaria" para orientar mejor cada módulo.

El archivo YAML también admite pesos por palabra clave, así las frases más específicas pueden ganar prioridad frente a términos genéricos.

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

La subida desde el frontend procesa solo los archivos nuevos y evita reconstruir todo el corpus en cada request.

Debajo de la carga de documentos hay una opción de reindexación que reutiliza el mismo proveedor y modelo configurados para la carga.

La ingesta añade metadatos como `manual_code` y `document_title` para ayudar a que la recuperación favorezca el manual más específico.

Script manual:

```powershell
python -m scripts.ingest
```

Si necesitas reconstruir desde cero el índice y volver a procesar los documentos, usa el script de rebuild:

```powershell
python -m scripts.rebuild_index
```

## Endpoints útiles

- `GET /health`: estado de la API.
- `POST /api/v1/ask`: responde preguntas sobre los manuales.
- `POST /api/v1/ingest`: recibe archivos y vuelve a generar el índice.

## Reglas de trabajo

- Siempre se debe actualizar este archivo cuando se realice alguna modificacion relevante en el proyecto. Asimismo debe actualizarse README.md y plan-accion.md.
- No tocar archivos fuera de `agente-alura-rag`.
- Mantener el `.gitignore` actualizado para no versionar el entorno virtual ni artefactos locales.
- No sobrescribir `data/processed/` manualmente salvo cuando se quiera reconstruir el índice.
- Antes de cambiar el flujo RAG, validar que `tests/test_health.py` siga pasando.

## Siguientes mejoras previstas

- Afinar la UI para mostrar métricas de carga e indexación.
- Mejorar manejo de errores en la carga de archivos.
- Agregar más pruebas para ingesta, embeddings y respuesta del chat.
- Mantener documentación sincronizada con el comportamiento real del código.
