from sqlalchemy import text
from app.core.database import get_active_engine

def add_new_columns():
    print("Migrating Supabase PostgreSQL schema...")
    with get_active_engine().connect() as conn:
        conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 8.0;"))
        conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS fluency_feedback TEXT;"))
        conn.execute(text("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS filler_words_detected JSON DEFAULT '[]'::json;"))
        conn.commit()
    print("[OK] Columns 'confidence_score', 'fluency_feedback', 'filler_words_detected' added successfully!")

if __name__ == "__main__":
    add_new_columns()
