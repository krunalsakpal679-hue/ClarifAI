"""
ClarifAI Groq LLM Completion Router
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.llm import LLMCompletionRequest, LLMCompletionResponse
from app.services.llm_client import generate_llm_completion
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["LLM Completion"])


@router.post(
    "/llm-completion",
    response_model=LLMCompletionResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def llm_completion_endpoint(request: LLMCompletionRequest):
    """
    Internal endpoint for Groq LLM completion requests.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    result = generate_llm_completion(
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    return LLMCompletionResponse(**result)
