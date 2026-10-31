import sys
from sqlalchemy.orm import Session
from app.core.database import create_db_session, get_active_engine, Base
from app.models.question import Question

INITIAL_QUESTIONS = [
    # -------------------------------------------------------------
    # Java (OOP Fundamentals, Pillars, Interfaces, JVM, Collections)
    # -------------------------------------------------------------
    {
        "technology": "Java",
        "topic": "OOP Fundamentals & Core Pillars",
        "difficulty": "Easy",
        "question": "What is Object-Oriented Programming in Java, and what are the core pillars of OOP such as encapsulation, inheritance, polymorphism, and abstraction?",
        "expected_answer": "OOP models software around objects and classes. The 4 core pillars are: Encapsulation (bundling data and methods while hiding internal state via private fields/getters/setters), Abstraction (hiding implementation details using interfaces and abstract classes), Inheritance (reusing and extending class behavior via 'extends'), and Polymorphism (compile-time method overloading and runtime method overriding).",
        "keywords": ["Java", "OOP", "Encapsulation", "Abstraction", "Inheritance", "Polymorphism", "Pillars"]
    },
    {
        "technology": "Java",
        "topic": "Interfaces vs Abstract Classes",
        "difficulty": "Medium",
        "question": "In Java, what is the difference between an abstract class and an interface, and when would you choose one over the other?",
        "expected_answer": "An interface defines a behavioral contract and supports multiple inheritance of type (as well as default/static methods since Java 8). An abstract class can hold state (instance fields), constructors, and partial method implementations, but a class can only extend one abstract class. Use interfaces for decoupled API contracts and abstract classes for code reuse among closely related classes.",
        "keywords": ["Java", "Interface", "Abstract Class", "Multiple Inheritance", "Default Methods"]
    },
    {
        "technology": "Java",
        "topic": "JVM Memory Architecture",
        "difficulty": "Medium",
        "question": "Explain the difference between Stack and Heap memory in Java, and how does Garbage Collection identify unreachable objects?",
        "expected_answer": "Stack memory stores local primitive variables and method call frames for each thread in a LIFO manner. Heap memory stores all instantiated objects and instance variables shared across threads. Garbage Collection traces object references starting from GC Roots (thread stacks, static variables); any object unreachable from GC roots is marked for reclamation.",
        "keywords": ["Java", "JVM", "Stack", "Heap", "Garbage Collection", "GC Roots"]
    },
    {
        "technology": "Java",
        "topic": "Collections Framework",
        "difficulty": "Easy",
        "question": "What is the difference between ArrayList and LinkedList in Java, and how does a HashMap work internally?",
        "expected_answer": "ArrayList uses a dynamic resizing array providing O(1) indexed access but O(N) arbitrary insertions/deletions. LinkedList uses a doubly-linked list with O(1) insertions/deletions at nodes but O(N) traversal. HashMap stores key-value pairs in buckets using hashCode() % capacity to locate bucket index, handling collisions via linked lists and converting to Red-Black trees when bucket size exceeds 8 (Java 8+).",
        "keywords": ["Java", "Collections", "ArrayList", "LinkedList", "HashMap", "Collisions"]
    },
    {
        "technology": "Java",
        "topic": "Exception Handling & Multithreading",
        "difficulty": "Hard",
        "question": "Explain the difference between checked and unchecked exceptions in Java, and what is the purpose of the synchronized keyword?",
        "expected_answer": "Checked exceptions (subclasses of Exception excluding RuntimeException) are verified at compile-time and must be caught or declared thrown. Unchecked exceptions (subclasses of RuntimeException) occur at runtime due to logic or state errors. The synchronized keyword enforces mutual exclusion by acquiring the intrinsic lock (monitor) of an object, preventing concurrent thread execution within critical sections.",
        "keywords": ["Java", "Checked Exceptions", "Unchecked Exceptions", "RuntimeException", "Synchronized", "Thread Safety"]
    },
    {
        "technology": "Java",
        "topic": "String Immutability & Memory Pool",
        "difficulty": "Easy",
        "question": "Why are Strings immutable in Java, and how does the String Constant Pool optimize memory?",
        "expected_answer": "Strings are immutable for security, thread-safety, and caching hash codes in HashMaps. The String Constant Pool in the JVM Heap stores unique literal strings; identical string literals point to the same memory reference, reducing heap allocation overhead.",
        "keywords": ["Java", "String", "Immutability", "String Constant Pool", "Heap"]
    },
    {
        "technology": "Java",
        "topic": "Java Streams & Functional Interfaces",
        "difficulty": "Medium",
        "question": "What is a functional interface in Java, and how do Java Streams differ from traditional Collections?",
        "expected_answer": "A functional interface contains exactly one abstract method (annotated with @FunctionalInterface) and can be instantiated via lambda expressions or method references. Collections are in-memory data structures holding elements, whereas Streams are pipelines that compute data lazily on demand without modifying the underlying source.",
        "keywords": ["Java", "Functional Interface", "Lambda", "Stream API", "Lazy Evaluation"]
    },

    # -------------------------------------------------------------
    # Python (OOP, Dunder, Decorators, Generators, AsyncIO, Memory)
    # -------------------------------------------------------------
    {
        "technology": "Python",
        "topic": "OOP & Dunder Methods",
        "difficulty": "Easy",
        "question": "How does Object-Oriented Programming work in Python, and what are dunder methods such as __init__, __str__, and __repr__?",
        "expected_answer": "Python supports OOP through class blueprints and instance objects. Dunder (double underscore) methods implement special protocols and operator overloading: __init__ initializes instance attributes, __str__ returns a human-readable representation, and __repr__ returns an unambiguous representation used for debugging.",
        "keywords": ["Python", "OOP", "Dunder Methods", "__init__", "__str__", "__repr__"]
    },
    {
        "technology": "Python",
        "topic": "Decorators",
        "difficulty": "Easy",
        "question": "What is a decorator in Python and how do you apply one to a function?",
        "expected_answer": "A decorator is a function that takes another function as an argument and extends its behavior without explicitly modifying it. It uses the @decorator_name syntax.",
        "keywords": ["Python", "function", "wrapper", "@syntax", "higher-order function"]
    },
    {
        "technology": "Python",
        "topic": "Generators & Iterators",
        "difficulty": "Medium",
        "question": "What is the difference between an iterator and a generator in Python, and how does the yield keyword optimize memory?",
        "expected_answer": "An iterator is an object implementing __iter__ and __next__. A generator is a function containing yield that returns a generator iterator. Instead of computing and storing an entire sequence in memory, yield pauses execution and emits values lazily on demand.",
        "keywords": ["Python", "Generators", "Iterators", "yield", "Lazy Evaluation"]
    },
    {
        "technology": "Python",
        "topic": "AsyncIO",
        "difficulty": "Medium",
        "question": "Explain the event loop in Python AsyncIO and how async/await differs from traditional multi-threading.",
        "expected_answer": "The event loop manages cooperative multitasking by executing asynchronous tasks in a single thread, pausing on IO operations via await, whereas multi-threading relies on OS preemptive scheduling subject to GIL contention.",
        "keywords": ["Python", "event loop", "cooperative multitasking", "non-blocking IO", "GIL"]
    },
    {
        "technology": "Python",
        "topic": "Memory Management",
        "difficulty": "Hard",
        "question": "How does Python handle memory management, reference counting, and garbage collection for cyclic references?",
        "expected_answer": "Python uses reference counting as its primary memory management mechanism. When references drop to zero, memory is freed immediately. A generational garbage collector detects and cleans cyclic references.",
        "keywords": ["Python", "reference counting", "generational GC", "cyclic references", "PyObject"]
    },
    {
        "technology": "Python",
        "topic": "Mutable Default Arguments",
        "difficulty": "Easy",
        "question": "Why is using a mutable default argument like a list or dictionary considered an anti-pattern in Python functions?",
        "expected_answer": "Default arguments in Python are evaluated once at function definition time, not at invocation. If a mutable object like a list is modified, subsequent calls share that same modified object. The standard fix is defaulting to None and initializing inside the function.",
        "keywords": ["Python", "Mutable Defaults", "Function Arguments", "Anti-pattern"]
    },

    # -------------------------------------------------------------
    # C++ (OOP, Virtual Functions, RAII, Memory)
    # -------------------------------------------------------------
    {
        "technology": "C++",
        "topic": "OOP, Virtual Functions & vtable",
        "difficulty": "Medium",
        "question": "How does runtime polymorphism work in C++, and what is the role of the vtable and virtual destructors?",
        "expected_answer": "Runtime polymorphism is achieved via virtual functions. The compiler creates a virtual method table (vtable) per class and assigns a vptr to each instance pointing to the vtable. Virtual destructors ensure that deleting an object through a base pointer invokes the derived class destructor first, preventing resource leaks.",
        "keywords": ["C++", "Polymorphism", "Virtual Functions", "vtable", "vptr", "Virtual Destructor"]
    },
    {
        "technology": "C++",
        "topic": "RAII & Smart Pointers",
        "difficulty": "Medium",
        "question": "Explain the RAII idiom in C++ and how std::unique_ptr and std::shared_ptr manage memory automatically.",
        "expected_answer": "RAII (Resource Acquisition Is Initialization) ties resource ownership to object lifetime, ensuring automatic cleanup when an object goes out of scope. std::unique_ptr enforces exclusive single ownership with zero overhead, while std::shared_ptr uses reference-counted control blocks for shared ownership.",
        "keywords": ["C++", "RAII", "unique_ptr", "shared_ptr", "Smart Pointers"]
    },
    {
        "technology": "C++",
        "topic": "Move Semantics & Rvalue References",
        "difficulty": "Hard",
        "question": "What are rvalue references and move semantics in C++11, and how do they eliminate unnecessary deep copying?",
        "expected_answer": "Rvalue references (T&&) bind to temporary objects. Move semantics (via std::move and move constructors) transfer underlying resource pointers (such as heap buffers) from temporary objects rather than allocating and deep-copying memory.",
        "keywords": ["C++", "Move Semantics", "rvalue", "std::move", "Move Constructor"]
    },

    # -------------------------------------------------------------
    # JavaScript / TypeScript
    # -------------------------------------------------------------
    {
        "technology": "JavaScript",
        "topic": "OOP & Prototypal Inheritance",
        "difficulty": "Easy",
        "question": "How does Object-Oriented Programming and prototypal inheritance work in JavaScript compared to classical class-based languages?",
        "expected_answer": "JavaScript uses prototype chaining where objects inherit properties and methods directly from other objects via their [[Prototype]] link (__proto__). ES6 'class' syntax is syntactic architecture sugar over constructors and prototype delegation.",
        "keywords": ["JavaScript", "OOP", "Prototypes", "Prototypal Inheritance", "ES6 Classes"]
    },
    {
        "technology": "JavaScript",
        "topic": "Event Loop & Concurrency",
        "difficulty": "Medium",
        "question": "Explain how the JavaScript Event Loop coordinates the Call Stack, Microtask queue, and Macrotask queue.",
        "expected_answer": "The Call Stack executes synchronous code in a single thread. Asynchronous operations enqueue callbacks: Microtasks (Promise then/catch/finally, queueMicrotask) have higher priority and are completely drained after each stack frame before Macrotasks (setTimeout, setInterval, I/O) are processed.",
        "keywords": ["JavaScript", "Event Loop", "Call Stack", "Microtasks", "Macrotasks", "Promises"]
    },
    {
        "technology": "JavaScript",
        "topic": "Closures & Lexical Scope",
        "difficulty": "Medium",
        "question": "What is a closure in JavaScript, and what are practical use cases for closures?",
        "expected_answer": "A closure is a function bundled with references to its surrounding lexical scope, allowing the inner function to access outer variables even after the outer function has returned. Practical use cases include data privacy (private variables), function currying, and memoization.",
        "keywords": ["JavaScript", "Closures", "Lexical Scope", "Data Privacy"]
    },
    {
        "technology": "TypeScript",
        "topic": "Interfaces vs Type Aliases",
        "difficulty": "Easy",
        "question": "In TypeScript, what is the difference between an Interface and a Type alias, and when should you choose one over the other?",
        "expected_answer": "Interfaces can be merged (declaration merging) and are ideal for defining object shapes and public APIs. Type aliases can define unions, primitives, tuples, and mapped types. Prefer interfaces for OOP object contracts and types for complex type operations.",
        "keywords": ["TypeScript", "Interface", "Type Alias", "Declaration Merging", "Union Types"]
    },

    # -------------------------------------------------------------
    # DBMS & SQL
    # -------------------------------------------------------------
    {
        "technology": "DBMS",
        "topic": "ACID Properties",
        "difficulty": "Easy",
        "question": "What do the ACID properties stand for in relational databases?",
        "expected_answer": "ACID stands for Atomicity (all or nothing), Consistency (valid state transitions), Isolation (concurrent transaction independence), and Durability (persist state after commit).",
        "keywords": ["DBMS", "Atomicity", "Consistency", "Isolation", "Durability"]
    },
    {
        "technology": "DBMS",
        "topic": "Indexing",
        "difficulty": "Medium",
        "question": "How do B-Tree indexes improve database query performance and what are their trade-offs?",
        "expected_answer": "B-Tree indexes reduce search time complexity from O(N) sequential scan to O(log N) tree traversal. The trade-off is increased storage overhead and slower write (INSERT/UPDATE) performance due to index maintenance.",
        "keywords": ["DBMS", "B-Tree", "O(log N)", "index maintenance", "write overhead"]
    },
    {
        "technology": "SQL",
        "topic": "SQL Joins & Performance Optimization",
        "difficulty": "Medium",
        "question": "Explain the differences between INNER, LEFT, RIGHT, and FULL OUTER joins in SQL, and how would you optimize a slow join query?",
        "expected_answer": "INNER join returns matching records from both tables; LEFT join returns all left rows plus matching right rows; RIGHT join is the inverse; FULL OUTER returns all rows from both. Optimize slow joins by ensuring join keys have indexes, analyzing EXPLAIN query execution plans, filtering with WHERE prior to joining, and avoiding SELECT *.",
        "keywords": ["SQL", "Joins", "Optimization", "EXPLAIN", "Foreign Keys"]
    },

    # -------------------------------------------------------------
    # Operating Systems & Computer Networks
    # -------------------------------------------------------------
    {
        "technology": "Operating System",
        "topic": "Process vs Thread",
        "difficulty": "Easy",
        "question": "What is the difference between a process and a thread, and how do their memory models differ?",
        "expected_answer": "A process is an independent executing program with its own isolated address space, while a thread is the smallest unit of execution within a process that shares the process's code, data, and heap but has its own stack and registers.",
        "keywords": ["Operating System", "Process", "Thread", "Memory Isolation", "Context Switching"]
    },
    {
        "technology": "Operating System",
        "topic": "Virtual Memory",
        "difficulty": "Hard",
        "question": "What is thrashing in operating systems and how is it related to page replacement algorithms?",
        "expected_answer": "Thrashing occurs when an OS spends more time swapping pages in/out of virtual memory than executing instructions due to inadequate working set allocation.",
        "keywords": ["Operating System", "Thrashing", "Page fault", "Working set", "Virtual memory"]
    },
    {
        "technology": "Computer Networks",
        "topic": "TCP/IP Handshake",
        "difficulty": "Easy",
        "question": "Explain the TCP 3-Way Handshake mechanism.",
        "expected_answer": "The TCP 3-Way Handshake establishes a reliable connection using SYN, SYN-ACK, and ACK packets between client and server.",
        "keywords": ["Computer Networks", "SYN", "SYN-ACK", "ACK", "Connection establishment"]
    },
    {
        "technology": "Computer Networks",
        "topic": "TCP vs UDP",
        "difficulty": "Easy",
        "question": "What are the primary differences between TCP and UDP protocols, and when would you choose UDP over TCP?",
        "expected_answer": "TCP is connection-oriented, reliable, guarantees packet ordering, and implements congestion control. UDP is connectionless, lightweight, and transmits without delivery guarantees. Use UDP when low latency is critical (e.g., live audio/video streaming, gaming).",
        "keywords": ["Computer Networks", "TCP", "UDP", "Reliability", "Latency"]
    },

    # -------------------------------------------------------------
    # Machine Learning & HR
    # -------------------------------------------------------------
    {
        "technology": "Machine Learning",
        "topic": "Overfitting",
        "difficulty": "Medium",
        "question": "What is overfitting in Machine Learning and how can regularization prevent it?",
        "expected_answer": "Overfitting occurs when a model learns training data noise rather than general patterns. L1 (Lasso) and L2 (Ridge) regularization penalize large weights to simplify the model.",
        "keywords": ["Machine Learning", "Overfitting", "Generalization", "L1 Regularization", "L2 Regularization"]
    },
    {
        "technology": "HR",
        "topic": "Conflict Resolution",
        "difficulty": "Easy",
        "question": "Describe a situation where you had a conflict with a teammate and how you resolved it.",
        "expected_answer": "Uses the STAR method (Situation, Task, Action, Result) to demonstrate active listening, empathy, open communication, and compromise.",
        "keywords": ["HR", "STAR method", "Communication", "Empathy", "Resolution"]
    }
]

def seed_database():
    active_engine = get_active_engine()
    Base.metadata.create_all(bind=active_engine)
    db: Session = create_db_session()
    try:
        added_count = 0
        skipped_count = 0
        for q_data in INITIAL_QUESTIONS:
            exists = db.query(Question).filter(
                Question.technology.ilike(q_data["technology"]),
                Question.topic.ilike(q_data["topic"]),
                Question.question == q_data["question"]
            ).first()
            if not exists:
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
                added_count += 1
            else:
                skipped_count += 1
        db.commit()
        print(f"Successfully seeded Question Bank: {added_count} new questions added, {skipped_count} existing retained. Total catalog: {len(INITIAL_QUESTIONS)}.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
