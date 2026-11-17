from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# ── Database connection ────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base         = declarative_base()


# ── Table 1: every call gets one row ──────────────────────
class CallReport(Base):
    __tablename__ = "call_reports"

    id             = Column(Integer,  primary_key=True, index=True)
    call_id        = Column(String,   unique=True, index=True)  # unique ID per call
    customer_name  = Column(String,   default="Unknown")
    intent         = Column(String)   # "inquiry" or "complaint"
    issue_category = Column(String)   # "network", "billing", "hardware" etc
    transcript     = Column(Text)     # full conversation text
    resolution     = Column(Text)     # what the AI did / said
    resolved       = Column(Boolean,  default=False)
    timestamp      = Column(DateTime, default=datetime.utcnow)


# ── Table 2: fired when same issue repeats too many times ──
class RecurringAlert(Base):
    __tablename__ = "recurring_alerts"

    id             = Column(Integer,  primary_key=True, index=True)
    issue_category = Column(String)   # which issue triggered the alert
    occurrences    = Column(Integer)  # how many times it appeared
    window_minutes = Column(Integer)  # within what time window
    alert_sent_at  = Column(DateTime, default=datetime.utcnow)
    report_summary = Column(Text)     # full summary sent to admin


# ── Create tables in PostgreSQL ────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created: call_reports, recurring_alerts")


# ── Get a DB session (used by all other files) ─────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()