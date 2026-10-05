import sys
from sqlalchemy.orm import Session
from app.core.database import create_db_session, get_active_engine, Base
from app.models.question import Question

INITIAL_QUESTIONS = [
    # Python
    {
        "technology": "Python",
        "topic": "Decorators",
        "difficulty": "Easy",
        "question": "What is a decorator in Python and how do you apply one to a function?",
        "expected_answer": "A decorator is a function that takes another function as an argument and extends its behavior without explicitly modifying it. It uses the @decorator_name syntax.",
        "keywords": ["function", "wrapper", "@syntax", "higher-order function"]
    },
    {
        "technology": "Python",
        "topic": "AsyncIO",
        "difficulty": "Medium",
        "question": "Explain the event loop in Python AsyncIO and how async/await differs from traditional multi-threading.",
        "expected_answer": "The event loop manages cooperative multitasking by executing asynchronous tasks in a single thread, pausing on IO operations via await, whereas multi-threading relies on OS preemptive scheduling subject to GIL contention.",
        "keywords": ["event loop", "cooperative multitasking", "non-blocking IO", "GIL"]
    },
    {
        "technology": "Python",
        "topic": "Memory Management",
        "difficulty": "Hard",
        "question": "How does Python handle memory management, reference counting, and garbage collection for cyclic references?",
        "expected_answer": "Python uses reference counting as its primary memory management mechanism. When references drop to zero, memory is freed immediately. A generational garbage collector detects and cleans cyclic references.",
        "keywords": ["reference counting", "generational GC", "cyclic references", "PyObject"]
    },
    # DBMS
    {
        "technology": "DBMS",
        "topic": "ACID Properties",
        "difficulty": "Easy",
        "question": "What do the ACID properties stand for in relational databases?",
        "expected_answer": "ACID stands for Atomicity (all or nothing), Consistency (valid state transitions), Isolation (concurrent transaction independence), and Durability (persist state after commit).",
        "keywords": ["Atomicity", "Consistency", "Isolation", "Durability"]
    },
    {
        "technology": "DBMS",
        "topic": "Indexing",
        "difficulty": "Medium",
        "question": "How do B-Tree indexes improve database query performance and what are their trade-offs?",
        "expected_answer": "B-Tree indexes reduce search time complexity from O(N) sequential scan to O(log N) tree traversal. The trade-off is increased storage overhead and slower write (INSERT/UPDATE) performance due to index maintenance.",
        "keywords": ["B-Tree", "O(log N)", "index maintenance", "write overhead"]
    },
    # Java
    {
        "technology": "Java",
        "topic": "Collections Framework",
        "difficulty": "Easy",
        "question": "What is the difference between ArrayList and LinkedList in Java?",
        "expected_answer": "ArrayList is backed by a dynamic array providing O(1) random access, whereas LinkedList is a doubly-linked list providing O(1) insertions/deletions at ends but O(N) element lookup.",
        "keywords": ["ArrayList", "LinkedList", "Dynamic Array", "Doubly-Linked List", "Time Complexity"]
    },
    {
        "technology": "Java",
        "topic": "Garbage Collection",
        "difficulty": "Medium",
        "question": "Explain the difference between Eden, Survivor, and Tenured spaces in JVM heap memory.",
        "expected_answer": "JVM heap is divided into Young Generation (Eden space and two Survivor spaces) for short-lived objects and Old/Tenured Generation for long-lived objects promoted after surviving multiple GC cycles.",
        "keywords": ["JVM Heap", "Young Generation", "Eden", "Tenured", "Promotion"]
    },
    # Computer Networks
    {
        "technology": "Computer Networks",
        "topic": "TCP/IP",
        "difficulty": "Easy",
        "question": "Explain the TCP 3-Way Handshake mechanism.",
        "expected_answer": "The TCP 3-Way Handshake establishes a reliable connection using SYN, SYN-ACK, and ACK packets between client and server.",
        "keywords": ["SYN", "SYN-ACK", "ACK", "Connection establishment"]
    },
    # Machine Learning
    {
        "technology": "Machine Learning",
        "topic": "Overfitting",
        "difficulty": "Medium",
        "question": "What is overfitting in Machine Learning and how can regularization prevent it?",
        "expected_answer": "Overfitting occurs when a model learns training data noise rather than general patterns. L1 (Lasso) and L2 (Ridge) regularization penalize large weights to simplify the model.",
        "keywords": ["Overfitting", "Generalization", "L1 Regularization", "L2 Regularization"]
    },
    # Operating System
    {
        "technology": "Operating System",
        "topic": "Virtual Memory",
        "difficulty": "Hard",
        "question": "What is thrashing in operating systems and how is it related to page replacement algorithms?",
        "expected_answer": "Thrashing occurs when an OS spends more time swapping pages in/out of virtual memory than executing instructions due to inadequate working set allocation.",
        "keywords": ["Thrashing", "Page fault", "Working set", "Virtual memory"]
    },
    # HR
    {
        "technology": "HR",
        "topic": "Conflict Resolution",
        "difficulty": "Easy",
        "question": "Describe a situation where you had a conflict with a teammate and how you resolved it.",
        "expected_answer": "Uses the STAR method (Situation, Task, Action, Result) to demonstrate active listening, empathy, open communication, and compromise.",
        "keywords": ["STAR method", "Communication", "Empathy", "Resolution"]
    }
]

def seed_database():
    Base.metadata.create_all(bind=get_active_engine())
    db: Session = create_db_session()
    try:
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} questions. Skipping seed.")
            return

        for q_data in INITIAL_QUESTIONS:
            q = Question(
                technology=q_data["technology"],
                topic=q_data["topic"],
                difficulty=q_data["difficulty"],
                question=q_data["question"],
                expected_answer=q_data["expected_answer"],
                keywords=q_data["keywords"],
                llm_generated=False,
                active=True
            )
            db.add(q)
        db.commit()
        print(f"Successfully seeded {len(INITIAL_QUESTIONS)} questions into the Question Bank.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
