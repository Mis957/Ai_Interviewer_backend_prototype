import logging
from threading import Lock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("uvicorn")


def _create_engine(db_url):
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300
    )


_primary_engine = _create_engine(settings.DATABASE_URL)
_offline_engine = (
    _create_engine(settings.OFFLINE_DATABASE_URL)
    if settings.OFFLINE_DATABASE_URL != settings.DATABASE_URL
    else None
)
_active_engine = _primary_engine
_using_offline_database = False
_engine_lock = Lock()

# Retained for scripts that need the configured primary engine directly.
engine = _primary_engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_primary_engine)

Base = declarative_base()


def _check_connection(eng):
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))


def get_active_engine():
    """Use the hosted database until it fails, then pin this process to local Supabase."""
    global _active_engine, _using_offline_database

    if _using_offline_database or _primary_engine.dialect.name == "sqlite":
        return _active_engine

    try:
        _check_connection(_primary_engine)
        return _primary_engine
    except SQLAlchemyError as primary_error:
        with _engine_lock:
            if _using_offline_database:
                return _active_engine

            if _offline_engine is None:
                raise RuntimeError(
                    "The primary database is unavailable and OFFLINE_DATABASE_URL "
                    "does not point to a separate local Supabase database."
                ) from primary_error

            try:
                _check_connection(_offline_engine)
            except SQLAlchemyError as offline_error:
                raise RuntimeError(
                    "The primary database is unavailable and local Supabase could "
                    "not be reached. Start the local Supabase stack and try again."
                ) from offline_error

            initialize_database_schema(_offline_engine)
            _active_engine = _offline_engine
            _using_offline_database = True
            logger.warning(
                "Primary database is unavailable; using local Supabase for this "
                "process. Local changes will not be synchronized automatically."
            )
            return _active_engine


def is_using_offline_database():
    return _using_offline_database


def create_db_session():
    return SessionLocal(bind=get_active_engine())


def ensure_database_schema(eng):
    with eng.connect() as conn:
        driver = eng.url.drivername
        if "postgresql" in driver:
            conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 8.0;"))
            conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS fluency_feedback TEXT;"))
            conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS missing_topics JSONB;"))
            conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS filler_words_detected JSONB;"))
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS mode VARCHAR(50) DEFAULT 'standard';"))
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS target_role VARCHAR(255);"))
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS years_of_experience VARCHAR(50);"))
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS resume_text TEXT;"))
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS resume_data JSONB;"))
            conn.execute(text("ALTER TABLE interview_sessions ALTER COLUMN technology TYPE VARCHAR(255);"))
            conn.execute(text("ALTER TABLE questions ALTER COLUMN technology TYPE VARCHAR(255);"))
            conn.execute(text("ALTER TABLE questions ALTER COLUMN topic TYPE VARCHAR(255);"))
            conn.execute(text("ALTER TABLE generated_questions ALTER COLUMN technology TYPE VARCHAR(255);"))
            conn.execute(text("ALTER TABLE generated_questions ALTER COLUMN topic TYPE VARCHAR(255);"))
            conn.commit()
        elif "sqlite" in driver:
            res_ans = conn.execute(text("PRAGMA table_info(interview_answers)"))
            cols_ans = [row[1] for row in res_ans.fetchall()]
            if cols_ans:
                missing_ans = {
                    "confidence_score": "FLOAT DEFAULT 8.0",
                    "fluency_feedback": "TEXT",
                    "missing_topics": "JSON",
                    "filler_words_detected": "JSON"
                }
                for col_name, col_type in missing_ans.items():
                    if col_name not in cols_ans:
                        conn.execute(text(f"ALTER TABLE interview_answers ADD COLUMN {col_name} {col_type}"))

            res_sess = conn.execute(text("PRAGMA table_info(interview_sessions)"))
            cols_sess = [row[1] for row in res_sess.fetchall()]
            if cols_sess:
                missing_sess = {
                    "mode": "VARCHAR(50) DEFAULT 'standard'",
                    "target_role": "VARCHAR(255)",
                    "years_of_experience": "VARCHAR(50)",
                    "resume_text": "TEXT",
                    "resume_data": "JSON"
                }
                for col_name, col_type in missing_sess.items():
                    if col_name not in cols_sess:
                        conn.execute(text(f"ALTER TABLE interview_sessions ADD COLUMN {col_name} {col_type}"))
            conn.commit()


def initialize_database_schema(eng=None):
    active_engine = eng or get_active_engine()
    Base.metadata.create_all(bind=active_engine)
    ensure_database_schema(active_engine)


def get_db():
    db = create_db_session()
    try:
        yield db
    finally:
        db.close()
