"""
ClarifAI Chatbot Router (AI-PHASE-CHATBOT)
Exposes internal endpoint for contract-grounded conversational RAG chatbot Q&A.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.chatbot import ChatbotRequest, ChatbotResponse
from app.services.chatbot_service import generate_chatbot_answer, clear_session_memory
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1/chatbot", tags=["Chatbot Conversational RAG"])


@router.post(
    "/chat",
    response_model=ChatbotResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def chat_endpoint(request: ChatbotRequest):
    """
    Internal endpoint for contract-grounded conversational RAG chatbot Q&A.
    Returns grounded answer with source clause IDs or controlled no-answer response.
    """
    try:
        res = generate_chatbot_answer(
            session_id=request.session_id,
            user_id=request.user_id,
            document_id=request.document_id,
            question=request.question,
            top_k=request.top_k or 5
        )
        return ChatbotResponse(**res)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot answer generation failed: {exc}")


@router.delete(
    "/session/{session_id}",
    dependencies=[Depends(verify_internal_secret)]
)
async def clear_session_endpoint(session_id: str, user_id: str, document_id: str):
    """
    Internal endpoint to purge conversational history for a specific session.
    """
    try:
        clear_session_memory(session_id=session_id, user_id=user_id, document_id=document_id)
        return {"success": True, "message": f"Session memory cleared for session '{session_id}'."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to clear session memory: {exc}")
