from app.db.database import engine, Base
from app.db.models import Application, Review, EventLog

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
