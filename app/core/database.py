import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("uvicorn")

db_url = settings.DATABASE_URL
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    logger.warning(f"Failed to connect to primary database ({db_url}): {e}. Falling back to local SQLite database.")
    db_url = "sqlite:///./interview_prototype.db"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
        logger.warning(f"Database schema migration check error: {e}")

ensure_database_schema(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



