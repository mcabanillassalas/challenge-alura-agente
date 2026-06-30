# Exactus RAG Agent

Agente RAG en Python para consultar manuales PDF del ERP Exactus con FastAPI, LangChain, Chroma y un frontend en Streamlit.

## Resumen

El proyecto permite:

- cargar manuales PDF, CSV o DOCX desde la API o desde el frontend;
- indexar el contenido en un vectorstore local persistido en `data/processed/`;
- responder preguntas sobre los manuales con contexto recuperado;
- elegir proveedor y modelo para chat e ingesta;
- validar el servicio con endpoints simples y pruebas mínimas.
- priorizar el manual correcto en la recuperación usando metadatos del documento y una heurística de tema.
- extender fácilmente las reglas de enrutamiento desde `app/core/manual_routing.py`.
- editar el mapeo temático sin tocar Python, usando `app/core/manual_routing.yml`.

## Estructura principal

- `app/`: backend FastAPI, configuración, esquemas y servicios RAG.
- `frontend/`: interfaz Streamlit.
- `scripts/`: ingesta, reconstrucción de índice y smoke test.
- `data/raw/exactus/`: documentos fuente.
- `data/processed/`: vectorstore persistido.
- `docs/`: notas de arquitectura y preguntas.
- `tests/`: pruebas automáticas básicas.

## Requisitos

- Python 3.11.
- Un entorno virtual activo.
- `pip` actualizado.
- Opcional: Ollama, OpenAI o Gemini según el proveedor que vayas a usar.

## Instalación local

En Windows PowerShell:

```powershell
cd D:\DevALURA\challenge-alura-agente\agente-alura-rag
.\env3.11\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si prefieres crear un entorno nuevo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Variables de entorno

El archivo `.env` se carga automáticamente desde la raíz del proyecto.

### Configuración general

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
CHROMA_PERSIST_DIRECTORY=./data/processed
DOCS_PATH=./data/raw/exactus
TOP_K=4
CHUNK_SIZE=1200
CHUNK_OVERLAP=150
```

### Ollama

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_LLM_MODEL=qwen2.5-coder:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### OpenAI

```env
OPENAI_API_KEY=tu_api_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Gemini

```env
GEMINI_API_KEY=tu_api_key
GEMINI_CHAT_MODEL=gemini-2.5-flash
```

## Ingesta e índice

Coloca los manuales en `data/raw/exactus/` y ejecuta:

```powershell
python -m scripts.ingest
```

Si necesitas borrar el vectorstore y reconstruirlo desde cero:

```powershell
python -m scripts.rebuild_index
```

La carga desde el frontend indexa solo los archivos recién subidos; no rehace todo el corpus en cada envío.

Debajo de la sección de carga hay una acción de reindexación que reutiliza el mismo proveedor y modelo seleccionados para cargar documentos.

## Ejecutar la API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API expone:

- `GET /health`
- `POST /api/v1/ask`
- `POST /api/v1/ingest`

## Ejecutar el frontend

En otra terminal:

```powershell
streamlit run frontend/streamlit_app.py
```

La UI usa la API en `http://127.0.0.1:8000` por defecto. Si necesitas cambiarla, define `API_BASE_URL`.

## Ejemplos de uso

### Consultar la API

```powershell
curl -X POST http://localhost:8000/api/v1/ask `
  -H "Content-Type: application/json" `
  -d '{"question":"¿Cómo se crea una factura en Exactus?","llm_provider":"ollama","llm_model":"qwen2.5-coder:7b"}'
```

### Probar el estado del servicio

```powershell
curl http://localhost:8000/health
```

## Pruebas rápidas

```powershell
pytest
python -m scripts.smoke_test
```

## Arquitectura

El flujo general es:

1. Los documentos se almacenan en `data/raw/exactus/`.
2. La ingesta extrae texto, agrega metadatos del manual, lo divide en chunks y genera embeddings.
3. Los embeddings se persisten en Chroma dentro de `data/processed/`.
4. La API consulta el vectorstore, prioriza el manual más específico según la consulta y arma la respuesta con contexto recuperado.
5. El frontend Streamlit permite preguntar, cargar documentos y revisar fuentes.

Las reglas temáticas viven en `app/core/manual_routing.py`, así que puedes agregar nuevas palabras clave o nuevos manuales sin tocar la lógica principal del RAG.

Si prefieres editar el mapa desde un archivo, usa `app/core/manual_routing.yml`.

Ejemplos útiles para ampliar el mapa: "alta de usuarios", "asignar permisos", "kardex", "movimiento de inventario", "conciliación bancaria" y "cálculo de nómina".

El archivo YAML admite pesos por regla, así que las frases más específicas pueden tener prioridad sobre palabras sueltas.

Para más detalle, revisa [docs/architecture.md](docs/architecture.md) y [plan-accion.md](plan-accion.md).

## Notas

- El provider por defecto del backend es `ollama`.
- La selección de modelo también se puede hacer desde el frontend.
- Los archivos subidos se guardan en `data/raw/exactus/` antes de reindexar.
- Gemini en este proyecto usa `langchain-google-genai==2.1.12`, fijado para ser compatible con el stack de LangChain del repo.
- No sobrescribas manualmente `data/processed/` salvo que quieras reconstruir el índice.
