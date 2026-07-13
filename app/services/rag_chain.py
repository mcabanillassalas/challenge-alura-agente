from app.core.config import settings
from app.core.manual_routing import infer_manual_code, normalize_text
from app.core.prompts import SYSTEM_PROMPT
from app.schemas.ask import AskResponse, SourceItem, MessageItem
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
    chat_history: list[MessageItem] = [],
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> AskResponse:
    # Si hay historial de chat, reformular la pregunta de seguimiento en una consulta independiente
    query_for_search = question
    if chat_history:
        llm = _get_llm(llm_provider, llm_model)
        history_str = "\n".join([f"{m.role}: {m.content}" for m in chat_history])
        condense_prompt = (
            "Dado el siguiente historial de conversación y una pregunta de seguimiento, "
            "reformula la pregunta para que sea una consulta de búsqueda independiente y completa en español "
            "que haga referencia clara a los temas discutidos anteriormente, sin pronombres y de forma directa. "
            "Genera únicamente la pregunta reformulada, nada de explicaciones ni introducciones adicionales.\n\n"
            f"Historial de conversación:\n{history_str}\n\n"
            f"Pregunta de seguimiento: {question}\n\n"
            "Pregunta reformulada:"
        )
        try:
            response_condense = llm.invoke(condense_prompt)
            content_condense = response_condense.content if hasattr(response_condense, "content") else str(response_condense)
            query_for_search = content_condense.strip()
        except Exception:
            pass

    # Limpiar signos de interrogación y puntuación iniciales/finales para mejorar consistencia en embeddings
    clean_question = query_for_search.strip().strip("¿?¡!.,;\"'")
    
    vectorstore = get_vectorstore()
    target_manual_code = _infer_manual_code(clean_question)
    fetch_k = max(settings.top_k * 4, 8)
    search_kwargs = {"k": fetch_k}
    if target_manual_code:
        search_kwargs["filter"] = {"manual_code": target_manual_code}

    docs_with_scores = vectorstore.similarity_search_with_score(clean_question, **search_kwargs)

    if not docs_with_scores and target_manual_code:
        docs_with_scores = vectorstore.similarity_search_with_score(clean_question, k=fetch_k)

    docs = _rank_documents(clean_question, docs_with_scores)[: settings.top_k]

    if not docs:
        return AskResponse(
            answer="No se encontró contexto relevante en los manuales cargados.",
            sources=[],
        )

    # Expansión de contexto: Recuperar todas las partes de la página original y de la página siguiente (N+1)
    expanded_docs = []
    seen_keys = set()
    for doc in docs:
        source = doc.metadata.get("source")
        page = doc.metadata.get("page")
        if not source or page is None:
            expanded_docs.append(doc)
            continue

        # Recuperar todas las partes de la página original (N)
        key = (source, page)
        if key not in seen_keys:
            seen_keys.add(key)
            try:
                page_docs = vectorstore.similarity_search(
                    "",
                    k=4,
                    filter={"$and": [{"source": source}, {"page": page}]}
                )
                expanded_docs.extend(page_docs)
            except Exception:
                expanded_docs.append(doc)

        # Recuperar todas las partes de la página siguiente (N+1)
        next_key = (source, page + 1)
        if next_key not in seen_keys:
            seen_keys.add(next_key)
            try:
                next_page_docs = vectorstore.similarity_search(
                    "",
                    k=4,
                    filter={"$and": [{"source": source}, {"page": page + 1}]}
                )
                expanded_docs.extend(next_page_docs)
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
    history_context = ""
    if chat_history:
        history_context = "Historial de conversación reciente:\n" + "\n".join(
            [f"{m.role.capitalize()}: {m.content}" for m in chat_history[-6:]]
        ) + "\n\n"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{history_context}"
        f"Contexto recuperado:\n{context}\n\n"
        f"Pregunta actual del usuario: {question}\n\n"
        "Responde de forma clara y breve en español. "
        "Ten en cuenta que términos como 'agregar', 'crear' o 'ingresar' son sinónimos de 'registrar' en este contexto. "
        "Si la respuesta o el procedimiento relacionado no está en el contexto, dilo claramente y no inventes pasos."
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