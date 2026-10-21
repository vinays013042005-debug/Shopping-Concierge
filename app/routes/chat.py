from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/api/chat", tags=["AI Concierge Chat"])

@router.post("", response_model=ChatResponse)
def chat_with_concierge(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="User message cannot be empty.")
    
    try:
        response = recommendation_service.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating recommendations: {str(e)}")
