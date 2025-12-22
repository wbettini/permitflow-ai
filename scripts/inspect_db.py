from app.db.database import SessionLocal
from app.db.models import Application, Review, EventLog
import json


def show_db_contents():
    db = SessionLocal()

    print("\n=== Applications ===")
    apps = db.query(Application).all()
    for app in apps:
        print(
            f"ID: {app.id}, Session: {app.session_id}, Type: {app.permit_type}, Status: {app.status}")
        print(f"Data: {json.dumps(app.data, indent=2)}")

    print("\n=== Reviews ===")
    reviews = db.query(Review).all()
    for r in reviews:
        print(
            f"App ID: {r.application_id}, SME: {r.sme_type}, Decision: {r.decision}")
        print(f"Justification: {r.justification}")

    print("\n=== Event Logs ===")
    events = db.query(EventLog).all()
    for e in events:
        print(
            f"App ID: {e.application_id}, Event: {e.event_type}, Time: {e.timestamp}")
        print(f"Details: {e.details}")

    db.close()


if __name__ == "__main__":
    show_db_contents()
