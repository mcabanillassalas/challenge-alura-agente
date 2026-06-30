from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT
from app.schemas.ask import AskResponse, SourceItem
from app.services.vectorstore import get_vectorstore


def _get_llm(provider_override: str | None = None, model_override: str | None = None):
    provider = (provider_override or settings.llm_provider).lower().strip()
    model = (model_override or "").strip()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada")

        return ChatOpenAI(
            model=model or settings.openai_chat_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no está configurada")

        return ChatGoogleGenerativeAI(
            model=model or settings.gemini_chat_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model or settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )

    raise ValueError(f"Proveedor de LLM no soportado: {settings.llm_provider}")


def answer_question(
    question: str,
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> AskResponse:
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": settings.top_k})
    docs = retriever.invoke(question)

    if not docs:
        return AskResponse(
            answer="No se encontró contexto relevante en los manuales cargados.",
            sources=[],
        )

    context = "\n\n".join(
        [
            (
                f"Documento: {doc.metadata.get('source', 'desconocido')} | "
                f"Página: {doc.metadata.get('page', 'N/D')}\n"
                f"{doc.page_content}"
            )
            for doc in docs
        ]
    )

    llm = _get_llm(llm_provider, llm_model)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Contexto recuperado:\n{context}\n\n"
        f"Pregunta: {question}\n\n"
        "Responde de forma clara y breve en español. "
        "Si la respuesta no está explícitamente en el contexto, dilo claramente y no inventes pasos."
    )

    response = llm.invoke(prompt)

    sources = [
        SourceItem(
            source=doc.metadata.get("source", "desconocido"),
            page=doc.metadata.get("page"),
            excerpt=doc.page_content[:300],
        )
        for doc in docs
    ]

    content = response.content if hasattr(response, "content") else str(response)
    return AskResponse(answer=content, sources=sources)