import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
APP_TITLE = "RAG Agent"
APP_SUBTITLE = "Consultas sobre manuales PDF de ERP Exactus usando RAG"

PROVIDER_OPTIONS = {
    "ollama": ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "llama3.2:latest"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "openai": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
}

LOAD_PROVIDER_OPTIONS = {
    "ollama": ["nomic-embed-text", "mxbai-embed-large"],
    "gemini": ["gemini-embedding-2"],
    "openai": ["text-embedding-3-small", "text-embedding-3-large"],
}

DEFAULT_PROVIDER = "openai"

seccion_configuracion = True
seccion_carga_documentos = False
seccion_reindexacion = False
seccion_estado = False
seccion_proveedores = False
seccion_chat = False



st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📘",
    layout="wide",
)


def get_health() -> dict[str, Any]:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}



def ask_question(
    question: str, llm_provider: str, llm_model: str, chat_history: list[dict[str, str]] = []
) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ask",
        json={
            "question": question,
            "chat_history": chat_history,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def upload_documents(
    uploaded_files: list[Any], embedding_provider: str, embedding_model: str
) -> dict[str, Any]:
    files_payload = []
    for uploaded_file in uploaded_files:
        files_payload.append(
            (
                "files",
                (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream",
                ),
            )
        )

    response = requests.post(
        f"{API_BASE_URL}/api/v1/ingest",
        files=files_payload,
        data={
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()


def reindex_documents(embedding_provider: str, embedding_model: str) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/reindex",
        data={
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()



def render_sidebar() -> None:
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    st.sidebar.markdown("<h1 style='text-align: center; margin-top: 0px; margin-bottom: 0px;'>Asistente ERP Exactus</h1>", unsafe_allow_html=True)

    # st.sidebar.text_input("API Base URL", value=API_BASE_URL, disabled=True)

    llm_provider = os.getenv("LLM_PROVIDER", "(desde backend)")
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "(desde backend)")
    ollama_llm_model = os.getenv("OLLAMA_LLM_MODEL", "(desde backend)")
    ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "(desde backend)")
    

    st.sidebar.markdown("### Manuales cargados")
    st.sidebar.markdown(
        "- AS - Administracion de Sistema\n"
        "- CI - Control de Inventarios\n"
        "- CP - Cuentas por Pagar\n"
        "- CC - Cuentas por Cobrar\n"
        "- CG - Contabilidad General\n"
        "- FA - Facturacion\n"
        "- CN - Control de Nominas\n"
        "- CB - Control Bancario\n"
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown("### Sugerencias de consultas")
    st.sidebar.markdown(
        "- ¿Cómo se crea una factura en Exactus?\n"
        "- ¿Cómo registrar un cliente nuevo?\n"
        "- ¿Qué dice el manual sobre facturación?\n"
        "- ¿Cómo se manejan pedidos o inventario?"
    )

    st.sidebar.markdown("---")

    st.sidebar.title("Configuración")
    st.sidebar.caption("La UI consume la API FastAPI ya levantada.")

    def on_provider_change():
        if st.session_state.provider_selector != "openai":
            st.toast("⚠️ Por el momento no se puede cambiar de Proveedor")
            st.session_state.provider_selector = "openai"

    def on_model_change():
        if st.session_state.model_selector != "gpt-4o-mini":
            st.toast("⚠️ Por el momento no se puede cambiar de Modelo")
            st.session_state.model_selector = "gpt-4o-mini"

    selected_provider = st.sidebar.selectbox(
        "Proveedor de IA",
        options=["ollama", "gemini", "openai"],
        index=2,
        key="provider_selector",
        on_change=on_provider_change,
    )
    selected_model = st.sidebar.selectbox(
        "Modelo",
        options=PROVIDER_OPTIONS[selected_provider],
        index=0,
        key="model_selector",
        on_change=on_model_change
    )
    st.session_state["selected_provider"] = selected_provider
    st.session_state["selected_model"] = selected_model

    st.sidebar.markdown("---")

    # st.sidebar.text_input("API Base URL", value=API_BASE_URL, disabled=True)

    st.sidebar.markdown("### Estado del backend")
    health = get_health()
    if health.get("status") == "ok":
        st.sidebar.success(
            f"API activa: {health.get('app', 'app')} {health.get('version', '')}"
        )
    else:
        st.sidebar.error("No fue posible conectar con el backend")
        st.sidebar.json(health)    


    if seccion_carga_documentos == True:

        st.sidebar.markdown("### Carga de documentos")
        st.sidebar.caption(
            "Sube archivos PDF, CSV o DOCX. Se guardan en data/raw/exactus y se reindexan en data/processed."
        )
        load_embedding_provider = st.sidebar.selectbox(
            "Proveedor de IA para carga",
            options=["ollama", "gemini", "openai"],
            index=0,
            key="load_embedding_provider",
        )
        load_embedding_model = st.sidebar.selectbox(
            "Modelo para carga",
            options=LOAD_PROVIDER_OPTIONS[load_embedding_provider],
            index=0,
            key="load_embedding_model",
        )
        uploaded_files = st.sidebar.file_uploader(
            "Selecciona uno o varios archivos",
            type=["pdf", "csv", "docx"],
            accept_multiple_files=True,
        )
        if st.sidebar.button(
            "Guardar y generar índices",
            disabled=not uploaded_files,
            use_container_width=True,
        ):
            try:
                with st.spinner("Guardando archivos y generando embeddings..."):
                    ingest_result = upload_documents(
                        uploaded_files,
                        load_embedding_provider,
                        load_embedding_model,
                    )

                saved_files = ingest_result.get("saved_files", [])
                st.sidebar.success(
                    f"Carga completada con {load_embedding_provider}/{load_embedding_model}: {ingest_result.get('documents', 0)} documentos y {ingest_result.get('chunks', 0)} chunks."
                )
                if saved_files:
                    with st.sidebar.expander("Archivos guardados"):
                        for file_info in saved_files:
                            st.write(f"{file_info.get('filename')} -> {file_info.get('stored_as')}")
            except requests.HTTPError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                st.sidebar.error(f"Error al cargar documentos: {detail}")
            except Exception as exc:
                st.sidebar.error(f"Error al cargar documentos: {exc}")

        if st.sidebar.button(
            "Reindexar documentos",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    f"Reindexando documentos con {load_embedding_provider}/{load_embedding_model}..."
                ):
                    reindex_result = reindex_documents(
                        load_embedding_provider,
                        load_embedding_model,
                    )

                st.sidebar.success(
                    f"Reindexación completada con {load_embedding_provider}/{load_embedding_model}: {reindex_result.get('documents', 0)} documentos y {reindex_result.get('chunks', 0)} chunks."
                )
            except requests.HTTPError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                st.sidebar.error(f"Error al reindexar documentos: {detail}")
            except Exception as exc:
                st.sidebar.error(f"Error al reindexar documentos: {exc}")

    if seccion_proveedores == True:
        st.sidebar.markdown("### Proveedores")
        st.sidebar.write(f"**LLM_PROVIDER:** {llm_provider}")
        st.sidebar.write(f"**EMBEDDING_PROVIDER:** {embedding_provider}")
        st.sidebar.write(f"**OLLAMA_LLM_MODEL:** {ollama_llm_model}")
        st.sidebar.write(f"**OLLAMA_EMBEDDING_MODEL:** {ollama_embedding_model}")



def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hola. Soy tu asistente RAG para consultar manuales de Exactus. Haz una pregunta en español.",
                "sources": [],
            }
        ]



def render_header() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)



def render_chat() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            sources = message.get("sources", [])
            if sources:
                with st.expander("Fuentes recuperadas"):
                    for idx, source in enumerate(sources, start=1):
                        source_name = source.get("source", "desconocido")
                        page = source.get("page", "N/D")
                        excerpt = source.get("excerpt", "")
                        st.markdown(f"**{idx}. {source_name}** — página: {page}")
                        st.code(excerpt, language="text")



def main() -> None:
    st.markdown(
        """
        <style>
        footer {visibility: hidden;}
        .css-main-footer {
            position: fixed;
            bottom: 0px;
            left: 0;
            width: 100%;
            text-align: center;
            font-size: 12px;
            color: #888888;
            background-color: transparent;
            padding: 5px 0;
            z-index: 9999;
            transition: left 0.3s, width 0.3s;
        }
        /* Ajustar posición cuando la barra lateral está abierta */
        section[data-testid="stSidebar"][aria-expanded="true"] ~ .main .css-main-footer {
            left: 336px;
            width: calc(100% - 336px);
        }
        /* Elevar la caja de chat input */
        div[data-testid="stChatInput"] {
            bottom: 24px !important;
        }
        </style>
        <div class="css-main-footer">
           <h6> © Desarrollado por Max Cabanillas Salas, 2026 </h6>
        </div>
        """,
        unsafe_allow_html=True
    )
    init_state()
    render_sidebar()
    render_header()
    render_chat()

    llm_provider = st.session_state.get("selected_provider", DEFAULT_PROVIDER)
    llm_model = st.session_state.get(
        "selected_model", PROVIDER_OPTIONS[llm_provider][0]
    )

    question = st.chat_input("Escribe tu pregunta sobre Exactus...")

    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question, "sources": []}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Consultando manuales y generando respuesta..."):
                try:
                    # Obtener el historial excluyendo el último mensaje del usuario
                    history_payload = st.session_state.messages[:-1]
                    chat_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in history_payload
                        if m["role"] in ["user", "assistant"]
                    ]
                    result = ask_question(question, llm_provider, llm_model, chat_history)
                    answer = result.get("answer", "No se recibió respuesta.")
                    sources = result.get("sources", [])

                    st.markdown(answer)
                    if sources:
                        with st.expander("Fuentes recuperadas"):
                            for idx, source in enumerate(sources, start=1):
                                source_name = source.get("source", "desconocido")
                                page = source.get("page", "N/D")
                                excerpt = source.get("excerpt", "")
                                st.markdown(f"**{idx}. {source_name}** — página: {page}")
                                st.code(excerpt, language="text")

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        }
                    )
                except requests.HTTPError as exc:
                    detail = exc.response.text if exc.response is not None else str(exc)
                    error_message = f"Error HTTP al consultar la API: {detail}"
                    st.error(error_message)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )
                except Exception as exc:
                    error_message = f"Error al consultar la API: {exc}"
                    st.error(error_message)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )


if __name__ == "__main__":
    main()
