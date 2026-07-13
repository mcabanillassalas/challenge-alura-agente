from pydantic import BaseModel, Field


class MessageItem(BaseModel):
    role: str = Field(..., description="Rol del emisor: user o assistant")
    content: str = Field(..., description="Contenido del mensaje")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pregunta del usuario")
    chat_history: list[MessageItem] = Field(
        default=[],
        description="Historial de mensajes anteriores en la sesión",
    )
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
