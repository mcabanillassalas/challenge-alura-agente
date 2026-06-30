# Arquitectura base parametrizada

## Flujo general

1. Los manuales PDF de Exactus se almacenan en `data/raw/exactus/`.
2. El script de ingesta lee los documentos, los fragmenta y genera embeddings.
3. El proveedor de embeddings se define con `EMBEDDING_PROVIDER` en `.env`.
4. Los embeddings se almacenan en Chroma local.
5. La API FastAPI recibe preguntas del usuario.
6. El retriever busca fragmentos relevantes.
7. El modelo de respuesta puede usar OpenAI u Ollama según la configuración.

## Componentes

- FastAPI: capa de API.
- LangChain: orquestación RAG.
- Chroma: índice vectorial local.
- OpenAI u Ollama: proveedor parametrizado por `.env`.
