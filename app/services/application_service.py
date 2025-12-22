from sqlalchemy.orm import Session
from app.db.models import Application, Review, EventLog
from app.db.database import SessionLocal
import json
from datetime import datetime, timezone


class ApplicationService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def create_application(self, session_id: str, permit_type: str, initial_data: dict = None) -> Application:
        app = Application(
            session_id=session_id,
            permit_type=permit_type,
            status="draft",
            data=initial_data or {}
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        self.log_event(app.id, "app_started", {"permit_type": permit_type})
        return app

    def get_application(self, app_id: int) -> Application:
        return self.db.query(Application).filter(Application.id == app_id).first()

    def get_active_application_by_session(self, session_id: str) -> Application:
        # Assuming one active application per session for now
        return self.db.query(Application).filter(
            Application.session_id == session_id,
            Application.status.in_(["draft", "submitted", "reviewing"])
        ).order_by(Application.created_at.desc()).first()

    def update_application_data(self, app_id: int, data_update: dict) -> Application:
        app = self.get_application(app_id)
        if app:
            # Merge new data into existing data
            current_data = dict(app.data) if app.data else {}
            current_data.update(data_update)
            app.data = current_data
            self.db.commit()
            self.db.refresh(app)
        return app

    def submit_application(self, app_id: int) -> Application:
        app = self.get_application(app_id)
        if app:
            app.status = "submitted"
            self.db.commit()
            self.db.refresh(app)
            self.log_event(app.id, "app_submitted", {})
        return app

    def add_review(self, app_id: int, sme_type: str, decision: str, justification: str) -> Review:
        review = Review(
            application_id=app_id,
            sme_type=sme_type,
            decision=decision,
            justification=justification
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        self.log_event(app_id, "sme_decision", {
            "sme_type": sme_type,
            "decision": decision,
            "justification": justification
        })
        return review

    def log_event(self, app_id: int, event_type: str, details: dict):
        event = EventLog(
            application_id=app_id,
            event_type=event_type,
            details=details
        )
        self.db.add(event)
        self.db.commit()

    def close(self):
        self.db.close()
