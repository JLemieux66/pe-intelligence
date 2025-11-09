"""
Schemas for similar companies feedback system
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SimilarityFeedbackRequest(BaseModel):
    """Request schema for similarity feedback"""
    source_company_id: int
    target_company_id: int
    is_similar: bool  # True if user thinks they are similar, False if not
    feedback_reason: Optional[str] = None  # Optional explanation
    user_email: Optional[str] = None  # For tracking feedback quality

class SimilarityFeedbackResponse(BaseModel):
    """Response schema for feedback submission"""
    success: bool
    message: str
    feedback_id: Optional[int] = None

class FeedbackStats(BaseModel):
    """Statistics about similarity feedback"""
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    accuracy_score: Optional[float] = None  # If we have ground truth data