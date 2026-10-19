from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings
from backend.app.core.context import get_current_tenant_id

db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def on_engine_connect(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite when testing."""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session with tenant RLS context set."""
    db = SessionLocal()
    org_id = get_current_tenant_id()
    
    # In PostgreSQL, inject tenant context for Row-Level Security
    if org_id and not settings.DATABASE_URL.startswith("sqlite"):
        try:
            db.execute(f"SET LOCAL app.current_tenant_id = '{org_id}'")
        except Exception:
            pass
            
    try:
        yield db
    finally:
        db.close()
