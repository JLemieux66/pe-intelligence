"""
Similar Companies API Routes
AI-powered company similarity analysis endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database_models_v2 import get_session
from backend.auth import verify_admin_token
from backend.schemas.requests import SimilarCompaniesRequest
from backend.schemas.responses import SimilarCompaniesResponse
from backend.services.similar_companies_service import SimilarCompaniesService

router = APIRouter(prefix="/api", tags=["similar-companies"])


@router.post("/similar-companies", response_model=SimilarCompaniesResponse)
async def find_similar_companies(
    request: SimilarCompaniesRequest,
    admin: dict = Depends(verify_admin_token),
    session: Session = Depends(get_session)
):
    """
    Find similar companies based on input company IDs.
    
    Uses AI-powered weighted scoring algorithm across multiple dimensions:
    - Verticals/Sub-industries (18 points)
    - Industry tags (8 points) 
    - Sector (6 points)
    - Revenue (42 points)
    - Employee count (13 points)
    - Total funding (4 points)
    - Public/private status (4 points)
    - Geography (4 points)
    - Funding stage (1 point)
    
    Returns ranked list of similar companies with AI-generated reasoning.
    Requires authentication.
    """
    try:
        service = SimilarCompaniesService(session)
        return service.find_similar_companies(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar companies: {str(e)}")


@router.post("/similar-companies/feedback")
async def submit_similarity_feedback(
    feedback_data: dict,
    admin: dict = Depends(verify_admin_token),
    session: Session = Depends(get_session)
):
    """
    Submit feedback on similar company matches.
    
    This endpoint allows users to provide feedback on the quality of similar company matches,
    which can be used to improve the similarity algorithm over time.
    
    Expected feedback_data format:
    {
        "input_company_id": int,
        "match_company_id": int, 
        "feedback_type": "good_match" | "not_a_match",
        "notes": "optional feedback notes"
    }
    """
    try:
        from src.models.database_models_v2 import CompanySimilarityFeedback
        
        # Validate required fields
        input_company_id = feedback_data.get('input_company_id')
        match_company_id = feedback_data.get('match_company_id')
        feedback_type = feedback_data.get('feedback_type')
        
        if not all([input_company_id, match_company_id, feedback_type]):
            raise HTTPException(status_code=400, detail="Missing required fields: input_company_id, match_company_id, feedback_type")
        
        # Check if feedback already exists for this user
        user_email = admin.get('email', 'unknown')
        existing_feedback = session.query(CompanySimilarityFeedback).filter(
            CompanySimilarityFeedback.input_company_id == input_company_id,
            CompanySimilarityFeedback.match_company_id == match_company_id,
            CompanySimilarityFeedback.user_email == user_email
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.feedback_type = feedback_type
            print(f"Updated similarity feedback from {user_email}: {input_company_id} -> {match_company_id} = {feedback_type}")
        else:
            # Create new feedback
            new_feedback = CompanySimilarityFeedback(
                input_company_id=input_company_id,
                match_company_id=match_company_id,
                feedback_type=feedback_type,
                user_email=user_email
            )
            session.add(new_feedback)
            print(f"New similarity feedback from {user_email}: {input_company_id} -> {match_company_id} = {feedback_type}")
        
        session.commit()
        
        return {
            "status": "success",
            "message": "Feedback saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")