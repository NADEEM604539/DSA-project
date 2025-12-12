"""
db.py

Role: SQLAlchemy MySQL connection + session management
- Provides engine and SessionLocal
- Provides get_db() dependency for FastAPI
- init_db() to ensure all tables exist (used at startup)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from config import settings

# -----------------------------
# 1) Base declarative class
# -----------------------------
Base = declarative_base()

# -----------------------------
# 2) SQLAlchemy Engine
# -----------------------------
engine = create_engine(
    settings.database_url,
    echo=False,            # set True for SQL debugging
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_timeout=30,
    future=True
)

# -----------------------------
# 3) Session factory
# -----------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# For scoped_session (optional, only if using in threading)
scoped_session_factory = scoped_session(SessionLocal)

# -----------------------------
# 4) Dependency for FastAPI
# -----------------------------
def get_db():
    """
    Provide DB session for FastAPI dependency injection.
    Usage in endpoint:
    ```
    def endpoint(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# -----------------------------
# 5) Init DB
# -----------------------------
def init_db():
    """
    Call this at app startup to ensure all tables exist.
    Uses models.py Base metadata.
    """
    from models import Base as ModelsBase  # import your SQLAlchemy models
    print("Creating tables if not exist...")
    ModelsBase.metadata.create_all(bind=engine)
    print("[INFO] All tables are ready.")
