from app.core.config import settings
from app.core.manual_routing import infer_manual_code, normalize_text
from app.core.prompts import SYSTEM_PROMPT
from app.schemas.ask import AskResponse, SourceItem
from app.services.vectorstore import get_vectorstore


def _tokenize(text: str) -> set[str]:
    normalized = normalize_text(text)
    tokens = set(normalized.replace("/", " ").replace("-", " ").split())
    return {token for token in tokens if len(token) > 2}


def _infer_manual_code(question: str) -> str | None:
    return infer_manual_code(question)


def _rank_documents(question: str, docs_with_scores):
    question_tokens = _tokenize(question)
    target_manual_code = _infer_manual_code(question)

    if target_manual_code:
        filtered_docs = [
            item for item in docs_with_scores if item[0].metadata.get("manual_code") == target_manual_code
        ]
        if filtered_docs:
            docs_with_scores = filtered_docs

    ranked_docs = []
    for doc, distance in docs_with_scores:
        document_text = f"{doc.metadata.get('document_title', '')} {doc.page_content[:1200]}"
        document_tokens = _tokenize(document_text)
        overlap = len(question_tokens & document_tokens)
        embedding_score = 1 / (1 + float(distance))
        title_tokens = _tokenize(doc.metadata.get("document_title", ""))
        title_overlap = len(question_tokens & title_tokens)
        score = embedding_score + (0.12 * overlap) + (0.18 * title_overlap)
        ranked_docs.append((score, doc))

    ranked_docs.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in ranked_docs]


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
    target_manual_code = _infer_manual_code(question)
    fetch_k = max(settings.top_k * 4, 8)
    search_kwargs = {"k": fetch_k}
    if target_manual_code:
        search_kwargs["filter"] = {"manual_code": target_manual_code}

    docs_with_scores = vectorstore.similarity_search_with_score(question, **search_kwargs)

    if not docs_with_scores and target_manual_code:
        docs_with_scores = vectorstore.similarity_search_with_score(question, k=fetch_k)

    docs = _rank_documents(question, docs_with_scores)[: settings.top_k]

    if not docs:
        return AskResponse(
            answer="No se encontró contexto relevante en los manuales cargados.",
            sources=[],
        )

    # Expansión de contexto: Recuperar la página siguiente (N+1) si no fue ya incluida
    expanded_docs = []
    seen_keys = set()
    for doc in docs:
        source = doc.metadata.get("source")
        page = doc.metadata.get("page")
        if not source or page is None:
            expanded_docs.append(doc)
            continue

        key = (source, page)
        if key not in seen_keys:
            seen_keys.add(key)
            expanded_docs.append(doc)

        next_key = (source, page + 1)
        if next_key not in seen_keys:
            seen_keys.add(next_key)
            try:
                next_page_docs = vectorstore.similarity_search(
                    "",
                    k=1,
                    filter={"$and": [{"source": source}, {"page": page + 1}]}
                )
                if next_page_docs:
                    expanded_docs.append(next_page_docs[0])
            except Exception:
                pass

    context = "\n\n".join(
        [
            (
                f"Documento: {doc.metadata.get('source', 'desconocido')} | "
                f"Página: {doc.metadata.get('page', 'N/D')}\n"
                f"{doc.page_content}"
            )
            for doc in expanded_docs
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
        for doc in expanded_docs
    ]

    content = response.content if hasattr(response, "content") else str(response)
    return AskResponse(answer=content, sources=sources)