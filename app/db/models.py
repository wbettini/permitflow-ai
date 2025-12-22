from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    permit_type = Column(String)
    # draft, submitted, reviewing, approved, rejected
    status = Column(String, default="draft")
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(
        timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    reviews = relationship("Review", back_populates="application")
    events = relationship("EventLog", back_populates="application")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    sme_type = Column(String)  # cyber, infra, architecture
    decision = Column(String)  # approve, decline
    justification = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="reviews")


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey(
        "applications.id"), nullable=True)
    # app_started, sme_review_start, sme_decision, human_review_ready
    event_type = Column(String)
    details = Column(JSON, default={})
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="events")
