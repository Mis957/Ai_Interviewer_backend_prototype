import asyncio
import os
import edge_tts

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "test_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

SAMPLE_ANSWERS = [
    {
        "filename": "python_decorator_excellent.mp3",
        "topic": "Python Decorators",
        "quality": "Excellent",
        "text": "A decorator in Python is a higher-order function that takes another function as an argument and extends or modifies its behavior dynamically without altering the original source code. You apply a decorator using the @ symbol written right above the function definition."
    },
    {
        "filename": "java_primitives_wrapper_good.mp3",
        "topic": "Java Primitives & Wrappers",
        "quality": "Good",
        "text": "Java primitive types like int, double, and boolean store raw values directly in stack memory. Wrapper classes like Integer, Double, and Boolean wrap these primitives into objects so they can be used in Java collections such as ArrayList. Autoboxing automatically converts primitives to wrapper objects when needed."
    },
    {
        "filename": "dbms_acid_properties_weak.mp3",
        "topic": "DBMS ACID Properties",
        "quality": "Weak",
        "text": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Atomicity means all or nothing, and isolation means transactions don't interfere with each other."
    },
    {
        "filename": "python_decorator_hesitant_fillers.mp3",
        "topic": "Python Decorators (Hesitant with Fillers & Humming)",
        "quality": "Hesitant/Filler Words",
        "text": "Um, well, a decorator in Python, uh, is like a function, you know, that takes another function as an argument, um, and like wraps it to add extra functionality, hmm, without changing the original code, you know?"
    }
]

async def generate_all():
    print(f"Generating {len(SAMPLE_ANSWERS)} test audio files into '{AUDIO_DIR}'...\n")
    for sample in SAMPLE_ANSWERS:
        filepath = os.path.join(AUDIO_DIR, sample["filename"])
        voice = "en-US-ChristopherNeural"
        communicate = edge_tts.Communicate(sample["text"], voice)
        await communicate.save(filepath)
        print(f"[OK] Generated: {sample['filename']}")
        print(f"   Topic: {sample['topic']} | Quality: {sample['quality']}")
        print(f"   Saved at: {filepath}\n")

if __name__ == "__main__":
    asyncio.run(generate_all())
