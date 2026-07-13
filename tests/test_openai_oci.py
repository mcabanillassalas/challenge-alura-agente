import os
import sys

# Get the directory of this script (which will be the project root on OCI)
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Load env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from app.services.rag_chain import _get_llm, _tokenize, _rank_documents, _infer_manual_code
from app.services.vectorstore import get_vectorstore
from app.core.config import settings

vectorstore = get_vectorstore()
question = "Cómo registrar un cliente nuevo?"

# Reproduce rag_chain logic exactly
target_manual_code = _infer_manual_code(question)
fetch_k = max(settings.top_k * 4, 8)
search_kwargs = {"k": fetch_k}
if target_manual_code:
    search_kwargs["filter"] = {"manual_code": target_manual_code}

docs_with_scores = vectorstore.similarity_search_with_score(question, **search_kwargs)
docs = _rank_documents(question, docs_with_scores)[: settings.top_k]

# Expand context
expanded_docs = []
seen_keys = set()
for doc in docs:
    source = doc.metadata.get("source")
    page = doc.metadata.get("page")
    if not source or page is None:
        expanded_docs.append(doc)
        continue

    # Retrieve all chunks for the original page first, to make sure we don't have it truncated
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

    # Retrieve all chunks for the next page N+1
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

llm = _get_llm()
from app.core.prompts import SYSTEM_PROMPT
prompt = (
    f"{SYSTEM_PROMPT}\n\n"
    f"Contexto recuperado:\n{context}\n\n"
    f"Pregunta: {question}\n\n"
    "Responde de forma clara y breve en español. "
    "Si la respuesta no está explícitamente en el contexto, dilo claramente y no inventes pasos."
)

response = llm.invoke(prompt)
content = response.content if hasattr(response, "content") else str(response)

output_path = os.path.join(project_root, "llm_debug_oci.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("=== PROMPT SENT TO LLM ===\n")
    f.write(prompt)
    f.write("\n" + "="*80 + "\n")
    f.write("=== LLM RESPONSE ===\n")
    f.write(content)

print("Finished writing debug logs to", output_path)
