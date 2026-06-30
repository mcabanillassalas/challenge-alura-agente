from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pregunta del usuario")
    llm_provider: str | None = Field(
        default=None,
        description="Proveedor de IA para esta consulta: ollama, gemini u openai",
    )
    llm_model: str | None = Field(
        default=None,
        description="Modelo a usar para esta consulta",
    )


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
