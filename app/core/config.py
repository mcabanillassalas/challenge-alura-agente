from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Exactus RAG Agent"
    app_version: str = "0.2.0"

    llm_provider: str = "ollama"
    embedding_provider: str = "ollama"

    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.5-flash"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_llm_model: str = "qwen2.5-coder:7b"
    ollama_embedding_model: str = "nomic-embed-text"

    chroma_persist_directory: str = "./data/processed"
    data_path: str = "./data"
    docs_path: str = "./data/raw/exactus"
    chunk_size: int = 1200
    chunk_overlap: int = 150
    top_k: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()