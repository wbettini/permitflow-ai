from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.models import Application, Review, EventLog

# --- Pydantic Schemas for Serialization ---


class ReviewSchema(BaseModel):
    id: int
    application_id: int
    sme_type: Optional[str]
    decision: Optional[str]
    justification: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class EventLogSchema(BaseModel):
    id: int
    application_id: Optional[int]
    event_type: Optional[str]
    details: Optional[Dict[str, Any]]
    timestamp: Optional[datetime]

    class Config:
        from_attributes = True


class ApplicationSchema(BaseModel):
    id: int
    session_id: Optional[str]
    permit_type: Optional[str]
    status: Optional[str]
    data: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # We can include related items if we want, but keeping it simple for now to avoid recursion issues
    # reviews: List[ReviewSchema] = []
    # events: List[EventLogSchema] = []

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/db",
    tags=["Database Inspector"],
    responses={404: {"description": "Not found"}},
)


@router.get("/applications", response_model=List[ApplicationSchema])
def read_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all applications.
    """
    applications = db.query(Application).offset(skip).limit(limit).all()
    return applications


@router.get("/reviews", response_model=List[ReviewSchema])
def read_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all reviews.
    """
    reviews = db.query(Review).offset(skip).limit(limit).all()
    return reviews


@router.get("/event_logs", response_model=List[EventLogSchema])
def read_event_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all event logs.
    """
    logs = db.query(EventLog).offset(skip).limit(limit).all()
    return logs
