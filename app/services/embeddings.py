from __future__ import annotations

from typing import List

import requests
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class CustomOllamaEmbeddings(Embeddings):
    def __init__(self, model: str, base_url: str, timeout: int = 120) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _embed_one(self, text: str) -> List[float]:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.model,
                "input": text,
            },
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(
                f"Error Ollama embed {response.status_code}: {response.text[:500]}"
            )
        data = response.json()
        return data["embeddings"][0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)



def get_embeddings_model(
    provider_override: str | None = None,
    model_override: str | None = None,
    base_url_override: str | None = None,
):
    provider = (provider_override or settings.embedding_provider).lower().strip()

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada")

        return OpenAIEmbeddings(
            model=model_override or settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no está configurada")

        return GoogleGenerativeAIEmbeddings(
            model=model_override or "text-embedding-004",
            google_api_key=settings.gemini_api_key,
        )

    if provider == "ollama":
        return CustomOllamaEmbeddings(
            model=model_override or settings.ollama_embedding_model,
            base_url=base_url_override or settings.ollama_base_url,
            timeout=180,
        )

    raise ValueError(
        f"Proveedor de embeddings no soportado: {settings.embedding_provider}"
    )