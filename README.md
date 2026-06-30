# Exactus RAG Agent

Agente IA base para consultar manuales PDF del ERP Exactus usando Python, FastAPI, LangChain y Chroma.

## Proveedores soportados

La ingesta de embeddings puede usar OpenAI u Ollama según la variable `EMBEDDING_PROVIDER` definida en `.env`.

- `EMBEDDING_PROVIDER=openai`
- `EMBEDDING_PROVIDER=ollama`

## Instalación local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuración OpenAI

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=tu_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Configuración Ollama

```env
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Ingesta

Copia tus manuales PDF dentro de `data/raw/exactus/` y luego ejecuta:

```bash
python -m scripts.ingest
```

## Ejecutar API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
