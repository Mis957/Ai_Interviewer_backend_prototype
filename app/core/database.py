import logging
import time
from datetime import datetime, timezone
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
    if settings.OFFLINE_DATABASE_URL and settings.OFFLINE_DATABASE_URL != settings.DATABASE_URL
    else None
)
_active_engine = _primary_engine
_using_offline_database = False
_engine_lock = Lock()
_last_sync_attempt = 0.0
_last_sync_succeeded_at = None
_last_sync_error = None
_last_primary_attempt = 0.0
_last_primary_error = None
_sync_retry_interval_seconds = 30

# Retained for scripts that need the configured primary engine directly.
engine = _primary_engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_primary_engine)

Base = declarative_base()


def _check_connection(eng):
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))


def _safe_database_error(error):
    message = str(getattr(error, "orig", error))
    primary_url = getattr(_primary_engine, "url", None)
    for secret in (
        getattr(primary_url, "password", None),
        getattr(primary_url, "username", None),
    ):
        if secret:
            message = message.replace(secret, "<redacted>")
    primary_host = getattr(primary_url, "host", None)
    if primary_host:
        message = message.replace(primary_host, "<db-host>")
    return message


def get_active_engine():
    """Use local Supabase during outages and sync it when the hosted DB returns."""
    global _active_engine, _using_offline_database
    global _last_sync_attempt, _last_sync_succeeded_at, _last_sync_error
    global _last_primary_attempt, _last_primary_error

    if _primary_engine.dialect.name == "sqlite":
        return _active_engine

    with _engine_lock:
        now = time.monotonic()
        if (
            _last_primary_attempt > 0.0
            and now - _last_primary_attempt < _sync_retry_interval_seconds
        ):
            return _active_engine

        _last_primary_attempt = now
        try:
            _check_connection(_primary_engine)
        except SQLAlchemyError as primary_error:
            _last_primary_error = _safe_database_error(primary_error)
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

            if not _using_offline_database:
                initialize_database_schema(_offline_engine)
                _active_engine = _offline_engine
                _using_offline_database = True
                logger.warning(
                    "Primary database is unavailable; using local Supabase. "
                    "Hosted connection error: %s. Local changes will sync when "
                    "the primary database returns.",
                    _last_primary_error,
                )
            return _offline_engine

        _last_primary_error = None
        _active_engine = _primary_engine
        _using_offline_database = False

        if (
            _offline_engine is not None
            and (
                _last_sync_attempt == 0.0
                or now - _last_sync_attempt >= _sync_retry_interval_seconds
            )
        ):
            _last_sync_attempt = now
            offline_is_available = False
            try:
                _check_connection(_offline_engine)
                offline_is_available = True
            except SQLAlchemyError:
                # Local offline Supabase is not running; skip sync gracefully
                pass

            if offline_is_available:
                try:
                    _sync_local_data_to_primary(_offline_engine, _primary_engine)
                except (SQLAlchemyError, RuntimeError) as sync_error:
                    _last_sync_error = _safe_database_error(sync_error)
                    logger.warning(
                        "Could not sync local Supabase data to the hosted database (%s); "
                        "the local data is retained and synchronization will retry. "
                        "New database requests will use the hosted database.",
                        _last_sync_error,
                    )
                else:
                    _last_sync_error = None
                    _last_sync_succeeded_at = datetime.now(timezone.utc).isoformat()
                    logger.info(
                        "Local Supabase data synchronization to the hosted database "
                        "completed; local records were retained."
                    )

        return _primary_engine


def _sync_local_data_to_primary(local_engine, primary_engine):
    """Idempotently upsert local rows to the hosted database without deleting local rows."""
    from sqlalchemy.dialects.postgresql import insert as postgres_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    initialize_database_schema(local_engine)
    initialize_database_schema(primary_engine)
    dialect = primary_engine.dialect.name
    if dialect == "postgresql":
        insert_for_dialect = postgres_insert
    elif dialect == "sqlite":
        insert_for_dialect = sqlite_insert
    else:
        raise RuntimeError(
            f"Offline synchronization does not support the {dialect} database dialect."
        )

    with local_engine.connect() as source, primary_engine.begin() as destination:
        for table in Base.metadata.sorted_tables:
            rows = [
                dict(row._mapping)
                for row in source.execute(table.select()).fetchall()
            ]
            if not rows:
                continue

            primary_keys = list(table.primary_key.columns)
            if not primary_keys:
                raise RuntimeError(
                    f"Cannot synchronize {table.name}: it has no primary key."
                )
            update_columns = {
                column.name: getattr(insert_for_dialect(table).excluded, column.name)
                for column in table.columns
                if not column.primary_key
            }

            for offset in range(0, len(rows), 250):
                statement = insert_for_dialect(table).values(rows[offset:offset + 250])
                if update_columns:
                    statement = statement.on_conflict_do_update(
                        index_elements=primary_keys,
                        set_=update_columns,
                    )
                else:
                    statement = statement.on_conflict_do_nothing(
                        index_elements=primary_keys,
                    )
                destination.execute(statement)


def is_using_offline_database():
    return _using_offline_database


def get_offline_sync_status():
    if _offline_engine is None:
        return {"status": "not_configured", "last_synced_at": None, "error": None}
    if _last_sync_error:
        return {
            "status": "pending",
            "last_synced_at": _last_sync_succeeded_at,
            "error": _last_sync_error,
        }
    if _using_offline_database:
        return {
            "status": "waiting_for_connection",
            "last_synced_at": _last_sync_succeeded_at,
            "error": _last_primary_error,
        }
    if _last_primary_error:
        return {
            "status": "waiting_for_connection",
            "last_synced_at": _last_sync_succeeded_at,
            "error": _last_primary_error,
        }
    return {
        "status": "synced" if _last_sync_succeeded_at else "not_attempted",
        "last_synced_at": _last_sync_succeeded_at,
        "error": None,
    }


def create_db_session():
    return SessionLocal(bind=get_active_engine())


def ensure_database_schema(eng):
    try:
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
    except Exception as e:
        logger.warning("Database schema migration check warning: %s", e)


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
