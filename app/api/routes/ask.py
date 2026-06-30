from fastapi import APIRouter, HTTPException

from app.schemas.ask import AskRequest, AskResponse
from app.services.rag_chain import answer_question

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    try:
        return answer_question(
            payload.question,
            llm_provider=payload.llm_provider,
            llm_model=payload.llm_model,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}") from exc
