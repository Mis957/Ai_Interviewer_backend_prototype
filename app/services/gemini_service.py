import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.interview import GeminiEvalOutput

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

def _safe_float(val: Any, default: float = 7.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class GeminiService:
    def __init__(self) -> None:
        self.api_key: str = settings.GEMINI_API_KEY
        self.model_name: str = settings.GEMINI_MODEL
        self.client: Optional[Any] = None
        
        self.groq_model: str = settings.GROQ_MODEL
        self.groq_clients: List[Any] = []
        self._groq_call_index: int = 0
        self.task_groq_clients: Dict[str, List[Any]] = {
            "question_gen": [],
            "evaluation": [],
            "analysis": []
        }

        # Collect global Groq API keys
        raw_groq_keys: List[str] = []
        for raw_val in [settings.GROQ_API_KEY, getattr(settings, "GROQ_API_KEY_SECONDARY", "")]:
            if raw_val:
                raw_groq_keys.extend([k.strip() for k in raw_val.split(",") if k.strip()])

        if Groq is not None:
            for k in raw_groq_keys:
                if k and not k.startswith("your-"):
                    try:
                        g_client = Groq(api_key=k)
                        self.groq_clients.append(g_client)
                        logger.info(f"Initialized global Groq client for key ending in '...{k[-6:]}'")
                    except Exception as e:
                        logger.warning(f"Failed to initialize Groq client for key '...{k[-6:]}': {e}")

            # Initialize dedicated per-task Groq clients if configured
            task_key_map = {
                "question_gen": getattr(settings, "GROQ_QUESTION_GEN_API_KEY", ""),
                "evaluation": getattr(settings, "GROQ_EVALUATION_API_KEY", ""),
                "analysis": getattr(settings, "GROQ_ANALYSIS_API_KEY", "")
            }
            for t_name, t_key in task_key_map.items():
                if t_key and not t_key.startswith("your-"):
                    try:
                        t_client = Groq(api_key=t_key.strip())
                        self.task_groq_clients[t_name].append(t_client)
                        logger.info(f"Initialized dedicated Groq client for task '{t_name}' (key '...{t_key[-6:]}')")
                    except Exception as te:
                        logger.warning(f"Failed to initialize dedicated Groq client for task '{t_name}': {te}")

        # Primary groq_client reference for backward compatibility
        self.groq_client: Optional[Any] = self.groq_clients[0] if self.groq_clients else None

        # Per-Task API Provider Chain Lists
        self.question_gen_providers: List[str] = [p.strip().lower() for p in getattr(settings, "QUESTION_GEN_PROVIDERS", "groq,groq,gemini").split(",") if p.strip()]
        self.evaluation_providers: List[str] = [p.strip().lower() for p in getattr(settings, "EVALUATION_PROVIDERS", "groq,groq,gemini").split(",") if p.strip()]
        self.analysis_providers: List[str] = [p.strip().lower() for p in getattr(settings, "ANALYSIS_PROVIDERS", "groq,groq,gemini").split(",") if p.strip()]

        if self.api_key and not self.api_key.startswith("your-") and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Google GenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    def _call_groq(
        self,
        prompt: str,
        system_prompt: str = "Act as an expert technical interviewer.",
        task_type: Optional[str] = None
    ) -> str:
        """Helper to invoke Groq API directly using dedicated task key or round-robin global keys."""
        # Prefer dedicated task clients if available, otherwise use global clients pool
        candidate_clients = self.task_groq_clients.get(task_type, []) if task_type else []
        if not candidate_clients:
            candidate_clients = self.groq_clients

        if not candidate_clients:
            raise ValueError("No Groq clients are initialized.")
        
        # Pick client index for this call and advance counter
        idx = self._groq_call_index % len(candidate_clients)
        self._groq_call_index += 1
        client = candidate_clients[idx]

        max_tok = 800 if task_type in ("analysis", "evaluation") else 400
        response = client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_tok
        )
        return response.choices[0].message.content.strip()

    def _call_gemini(self, prompt: str, system_prompt: str = "Act as an expert technical interviewer.") -> str:
        """Helper to invoke Gemini API directly."""
        if self.client is None:
            raise ValueError("Gemini client is not initialized.")
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt
        )
        return response.text.strip()

    def _call_llm_for_task(
        self,
        task_type: str,
        prompt: str,
        system_prompt: str = "Act as an expert technical interviewer."
    ) -> str:
        """
        Executes LLM request by iterating over configured provider fallback chains for the specific task.
        task_type can be: 'question_gen', 'evaluation', 'analysis'
        """
        providers_map = {
            "question_gen": self.question_gen_providers,
            "evaluation": self.evaluation_providers,
            "analysis": self.analysis_providers
        }
        provider_chain = providers_map.get(task_type, ["groq", "gemini"])

        for provider in provider_chain:
            if provider == "groq":
                try:
                    out = self._call_groq(prompt, system_prompt, task_type=task_type)
                    if out:
                        logger.info(f"[{task_type}] Successfully fulfilled request via Groq API.")
                        return out
                except Exception as e:
                    logger.warning(f"[{task_type}] Groq provider failed: {e}. Attempting fallback...")
            elif provider in ("gemini", "google"):
                try:
                    out = self._call_gemini(prompt, system_prompt)
                    if out:
                        logger.info(f"[{task_type}] Successfully fulfilled request via Gemini API.")
                        return out
                except Exception as e:
                    logger.warning(f"[{task_type}] Gemini provider failed: {e}. Attempting fallback...")
            else:
                logger.debug(f"[{task_type}] Unknown or unconfigured provider '{provider}'. Skipping...")

        logger.warning(f"[{task_type}] All configured API providers ({provider_chain}) failed or were unavailable. Invoking offline task generator.")
        return ""

    def _call_llm(self, prompt: str, system_prompt: str = "Act as an expert technical interviewer.") -> str:
        """Backward compatible default LLM call method."""
        return self._call_llm_for_task("question_gen", prompt, system_prompt)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        # Strip thinking tags if model emitted them
        if "<think>" in text and "</think>" in text:
            text = text.split("</think>")[-1].strip()

        # Clean markdown formatting if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Extract JSON object substring if surrounded by prose
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx+1]

        # Attempt 1: Standard JSON parse with strict=False
        try:
            res = json.loads(text, strict=False)
            if isinstance(res, dict):
                return res
        except Exception:
            pass

        # Attempt 2: Escape unescaped line breaks inside double-quoted string values
        try:
            fixed_text = re.sub(
                r'"([^"\\]|\\.)*"',
                lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'),
                text,
                flags=re.DOTALL
            )
            res = json.loads(fixed_text, strict=False)
            if isinstance(res, dict):
                return res
        except Exception:
            pass

        # Attempt 3: Field-level regex extraction for damaged LLM output
        q_match = re.search(r'"question"\s*:\s*"([^"]+)"', text)
        topic_match = re.search(r'"topic"\s*:\s*"([^"]+)"', text)
        ans_match = re.search(r'"expected_answer"\s*:\s*"([^"]+)"', text)

        if q_match:
            return {
                "topic": topic_match.group(1) if topic_match else "Technical Concepts",
                "question": q_match.group(1),
                "expected_answer": ans_match.group(1) if ans_match else "Comprehensive technical explanation.",
                "keywords": []
            }

        raise ValueError("Could not parse LLM JSON output.")

    def evaluate_answer(
        self,
        question: str,
        expected_answer: str,
        candidate_answer: str
    ) -> GeminiEvalOutput:
        prompt = f"""
Act as an expert technical interviewer and speech fluency evaluator.
Evaluate the candidate's answer for technical accuracy AND speech fluency/delivery confidence (speech rate, humming, filler words, repeated words, long pauses).

Question: {question}
Expected Answer Key: {expected_answer}
Candidate's Spoken/Transcribed Answer: {candidate_answer}

Provide your evaluation STRICTLY in JSON format with NO markdown formatting or commentary:
{{
  "score": <float between 0.0 and 10.0 for technical accuracy>,
  "confidence_score": <float between 0.0 and 10.0 for speech fluency and delivery confidence>,
  "feedback": "<concise technical accuracy feedback>",
  "fluency_feedback": "<constructive feedback analyzing speech delivery, humming, filler words, pauses, and repetition>",
  "filler_words_detected": ["<filler_word_1>", "<filler_word_2>"],
  "missing_topics": ["<topic1>", "<topic2>"],
  "next_difficulty": "<Easy | Medium | Hard>"
}}

Scoring Guidelines for confidence_score:
- 9.0-10.0: Clear, fluent, confident delivery with virtually no filler words or hesitation.
- 6.5-8.9: Good delivery with minor hesitation or occasional filler words (e.g., "um", "uh", "like").
- 4.0-6.4: Frequent pauses, noticeable humming ("hmm", "err"), repeated words ("I I", "the the"), or hesitation.
- <4.0: Heavy humming, excessive breaks/silence, severe stuttering/word repetitions, or very low delivery confidence.

Rules for next_difficulty:
- If score >= 8.0: next_difficulty should be "Hard"
- If score >= 5.0 and score < 8.0: next_difficulty should be "Medium"
- If score < 5.0: next_difficulty should be "Easy"
"""
        raw_output = self._call_llm_for_task("evaluation", prompt)
        if raw_output:
            try:
                data = self._parse_json(raw_output)
                return GeminiEvalOutput(
                    score=_safe_float(data.get("score"), 7.0),
                    confidence_score=_safe_float(data.get("confidence_score"), 8.0),
                    feedback=str(data.get("feedback", "Good effort. Cover core principles deeper.")),
                    fluency_feedback=str(data.get("fluency_feedback", "Clear delivery with steady pace.")),
                    filler_words_detected=data.get("filler_words_detected") if isinstance(data.get("filler_words_detected"), list) else [],
                    missing_topics=data.get("missing_topics") if isinstance(data.get("missing_topics"), list) else [],
                    next_difficulty=str(data.get("next_difficulty", "Medium"))
                )
            except Exception as e:
                logger.error(f"Failed to parse LLM evaluation JSON: {e}")

        # Fallback Mock Evaluation for offline/mock testing
        cand_lower = candidate_answer.lower()
        cand_words = cand_lower.split()
        cand_len = len(cand_words)
        
        # Detect common filler words
        common_fillers = ["um", "uh", "hmm", "err", "like", "you know", "basically", "actually"]
        detected = [fw for fw in common_fillers if fw in cand_lower]
        
        conf_score = 9.0 if len(detected) == 0 else (7.0 if len(detected) <= 2 else 4.5)
        fluency = "Fluent delivery with clear expression." if conf_score >= 8.5 else f"Detected filler words ({', '.join(detected)}). Try to speak with fewer pauses."

        score = 8.5 if cand_len > 15 else (6.0 if cand_len > 5 else 4.0)
        next_diff = "Hard" if score >= 8.0 else ("Medium" if score >= 5.0 else "Easy")
        
        return GeminiEvalOutput(
            score=score,
            confidence_score=conf_score,
            feedback=f"Evaluated answer ({cand_len} words). Good fundamental understanding shown.",
            fluency_feedback=fluency,
            filler_words_detected=detected,
            missing_topics=["edge cases", "performance optimization"] if score < 8.0 else [],
            next_difficulty=next_diff
        )

    def generate_dynamic_question(
        self,
        technology: str,
        difficulty: str,
        existing_topics: Optional[List[str]] = None,
        target_role: Optional[str] = None,
        years_of_experience: Optional[str] = None,
        stage: Optional[str] = None,
        adaptive_mode: Optional[str] = None,
        previous_topic: Optional[str] = None,
        previous_score: Optional[float] = None
    ) -> Dict[str, Any]:
        avoid_str = ", ".join(existing_topics) if existing_topics else "None"
        role_str = target_role or "Software Developer"
        yoe_str = years_of_experience or "1-3 years"

        stage_instruction = ""
        stage_instruction = ""
        if stage in ("intro", "stage1_intro"):
            stage_instruction = f"""
STAGE 1 - INTRODUCTION & BACKGROUND (OPENING DIRECTIVE):
Goal: Warm up candidate and identify focal points to drill into later.
Ask the classic opening: "Walk me through your background and what you’ve been focusing on recently." (tailor slightly for candidate track: {technology}).
Set topic as "Candidate Introduction & Background".
"""
        elif stage in ("intro_followup", "stage1_intro_followup"):
            prev_top = previous_topic or technology
            stage_instruction = f"""
STAGE 1 - INTRODUCTION & BACKGROUND (FOLLOW-UP DIRECTIVE):
Goal: Follow up once to clarify a highlight before transitioning to project deep-dive.
Ask a clarifying follow-up based on their focus or previous topic '{prev_top}':
Ask: "You mentioned working heavily with {prev_top}—what drew you toward performance engineering or systems architecture over general application development?" (or tailored for {technology}).
Set topic as "Background Follow-up & Specialization".
"""
        elif stage in ("project", "stage2_project_deepdive"):
            vague_push = " Candidate's previous answer was vague or lacking depth, so EXPLICITLY push for specific metrics, profiling tools (e.g. nvprof, perf, valgrind), or architectural trade-offs." if (previous_score is not None and previous_score < 6.0) else ""
            stage_instruction = f"""
STAGE 2 - PROJECT DEEP-DIVE (DIRECTIVE):
Goal: Test technical authenticity, architecture decisions, and ownership.
Frame question around architectural trade-offs, bottlenecks, thread synchronization, memory allocation/divergence, and design decisions rather than just what the project does.{vague_push}
Example question style: "In your parallel optimization project, how did you handle thread synchronization and memory divergence across warps?"
Set topic as "Project Architecture & Engineering Trade-offs".
"""
        elif stage in ("technical_adaptive", "stage3_technical_fundamentals"):
            if adaptive_mode == "deep_dive" and previous_topic:
                stage_instruction = f"""
STAGE 3 - TECHNICAL FUNDAMENTALS & TECH STACK (GO DEEPER):
Goal: Test depth in declared languages, paradigms, and systems engineering.
Categorize into one of:
- Language Internals: Memory management, concurrency models, pointer arithmetic (e.g. C++ move semantics vs smart pointers, GIL / CPython memory allocation).
- Systems / Concurrency: Thread contention, latency vs throughput, distributed coordination (e.g. OpenMPI vs Ray task scheduling).
- Tooling / DevOps: Container isolation, orchestration nuances, or cloud provisioning.
The candidate did well on '{previous_topic}'. Drill down deeper into internal mechanics, memory/performance trade-offs, or edge cases of '{previous_topic}'.
"""
            elif adaptive_mode == "pivot" and previous_topic:
                stage_instruction = f"""
STAGE 3 - TECHNICAL FUNDAMENTALS & TECH STACK (PIVOT):
Goal: Test depth in declared languages, paradigms, and systems engineering.
The candidate struggled on '{previous_topic}'. Do NOT dwell on '{previous_topic}'. Pivot cleanly away to another category: Language Internals, Systems/Concurrency, or Tooling/DevOps.
"""
            else:
                stage_instruction = f"""
STAGE 3 - TECHNICAL FUNDAMENTALS & TECH STACK:
Goal: Test depth in declared languages, paradigms, and systems engineering for {technology}.
Categorize into one of:
1. Language Internals (memory management, concurrency models, move semantics vs smart pointers)
2. Systems / Concurrency (thread contention, latency vs throughput, OpenMPI vs Ray task scheduling)
3. Tooling / DevOps (container isolation, orchestration nuances, cloud provisioning)
Start at Medium difficulty.
"""

        prompt = f"""
Act as an expert human Technical Interviewer conducting a live interview.

Candidate Profile:
- Technology Track: {technology}
- Target Job Role: {role_str}
- Years of Experience: {yoe_str}
- Question Difficulty Level: {difficulty}
- Topics Already Covered in this Session (AVOID DUPLICATES): {avoid_str}

{stage_instruction}

IMPORTANT: Keep all JSON string values on single lines or use escaped \\n for line breaks. Do not output raw unescaped newlines inside string values.

Return STRICTLY in JSON format with NO markdown wrapping:
{{
  "topic": "<Specific Topic Name>",
  "question": "<Interview Question Text>",
  "expected_answer": "<Comprehensive Expected Answer>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}}
"""
        raw_output = self._call_llm_for_task("question_gen", prompt)
        if raw_output:
            try:
                data = self._parse_json(raw_output)
                if isinstance(data, dict):
                    question = data.get("question") or data.get("question_text") or data.get("title") or ""
                    if isinstance(question, dict):
                        question = question.get("text") or str(question)
                    if question:
                        return {
                            "topic": str(data.get("topic") or data.get("title") or data.get("category") or f"{technology} Concepts"),
                            "question": str(question),
                            "expected_answer": str(data.get("expected_answer") or data.get("solution") or data.get("exampleAnswer") or "Comprehensive technical explanation."),
                            "keywords": data.get("keywords") if isinstance(data.get("keywords"), list) else [technology, difficulty.lower()]
                        }
            except Exception as e:
                logger.error(f"Failed to parse LLM question generation JSON: {e}. Raw output: {repr(raw_output)}")

        # Dynamic fallback generator
        if stage in ("intro", "stage1_intro"):
            return {
                "topic": "Candidate Introduction & Background",
                "question": "Walk me through your background and what you’ve been focusing on recently.",
                "expected_answer": f"Candidate introduces themselves, highlights experience with {technology}, and describes recent technical focus.",
                "keywords": ["introduction", "background", technology]
            }
        elif stage in ("intro_followup", "stage1_intro_followup"):
            return {
                "topic": "Background Follow-up & Specialization",
                "question": f"You mentioned working heavily with {technology} and distributed systems—what drew you toward performance engineering and systems architecture over general application development?",
                "expected_answer": "Candidate articulates their motivation for performance engineering and systems architecture.",
                "keywords": [technology, "performance-engineering", "systems"]
            }

        return {
            "topic": f"{technology} Advanced Concepts",
            "question": f"Explain key architectural concepts and best practices in {technology} for {difficulty} level applications.",
            "expected_answer": f"Clear explanation of design patterns, error handling, memory management, and performance optimization in {technology}.",
            "keywords": [technology, "architecture", difficulty.lower(), "best-practices"]
        }

    def generate_resume_question(
        self,
        resume_data: Dict[str, Any],
        category: str,
        difficulty: str,
        existing_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates interview question specifically tailored to candidate's uploaded resume (3-Stage Flow):
        - Stage 1: intro (Classic Opening) & intro_followup (Clarifying follow-up)
        - Stage 2: project (Flagship project architecture, trade-offs, bottlenecks, thread sync)
        - Stage 3: skill (Language Internals, Systems/Concurrency, Tooling/DevOps from parsed_skills)
        """
        avoid_str = ", ".join(existing_topics) if existing_topics else "None"
        candidate_name = resume_data.get("candidate_name", "Candidate")
        skills_str = ", ".join(resume_data.get("skills", ["Software Engineering"]))
        projects = resume_data.get("projects", [])
        proj_str = json.dumps(projects)
        hr_topics_str = ", ".join(resume_data.get("hr_topics", ["Teamwork", "Problem Solving"]))

        category_instructions = ""
        if category == "intro":
            category_instructions = f"STAGE 1 OPENING: Ask the classic opening: 'Walk me through your background and what you’ve been focusing on recently.' Ask candidate '{candidate_name}' to introduce themselves, summarize their background in {skills_str}, and share a brief overview of their main projects."
        elif category == "intro_followup":
            category_instructions = f"STAGE 1 FOLLOW-UP: Follow up once to clarify a highlight before transitioning: Ask 'You mentioned working heavily with {skills_str}—what drew you toward performance engineering or systems architecture over general application development?'"
        elif category == "project" and projects:
            category_instructions = f"STAGE 2 PROJECT DEEP-DIVE: Extract flagship project(s) from resume ({proj_str}). Test technical authenticity, architecture decisions, trade-offs, bottlenecks, thread synchronization, memory divergence, and design choices (e.g. 'In your parallel optimization project, how did you handle thread synchronization and memory divergence across warps?'). If previous response was vague, explicitly push for specific metrics, profiling tools (e.g. nvprof, perf, valgrind), or architectural trade-offs."
        else:
            category_instructions = f"STAGE 3 TECHNICAL FUNDAMENTALS: Pull directly from parsed skills ({skills_str}). Categorize into Language Internals (memory management, move semantics vs smart pointers, pointer arithmetic), Systems / Concurrency (thread contention, latency vs throughput, OpenMPI vs Ray task scheduling), or Tooling / DevOps (container isolation, orchestration, cloud provisioning). Start at Medium difficulty and adapt."

        prompt = f"""
Act as an expert Technical & HR Interviewer conducting a resume-based interview for candidate '{candidate_name}'.

Candidate Skills: {skills_str}
Candidate Projects: {proj_str}
Candidate HR Scenarios: {hr_topics_str}

Target Focus Category: {category}
Question Difficulty: {difficulty}
Instructions: {category_instructions}
Topics Already Asked in this session (AVOID duplicate concepts/topics): {avoid_str}

IMPORTANT: Keep all JSON string values on single lines or use escaped \\n for line breaks.

Return STRICTLY in JSON format with NO markdown wrapping:
{{
  "topic": "<Specific Project Name or Skill Topic>",
  "category": "{category}",
  "question": "<Tailored Interview Question Text>",
  "expected_answer": "<Key points expected in candidate response>",
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
        raw_output = self._call_llm_for_task("question_gen", prompt)
        if raw_output:
            try:
                data = self._parse_json(raw_output)
                if isinstance(data, dict):
                    question = data.get("question") or data.get("question_text") or ""
                    if question:
                        return {
                            "topic": str(data.get("topic") or f"Resume {category.title()}"),
                            "category": category,
                            "question": str(question),
                            "expected_answer": str(data.get("expected_answer") or "Clear technical explanation with specific project context."),
                            "keywords": data.get("keywords") if isinstance(data.get("keywords"), list) else [category, difficulty.lower()]
                        }
            except Exception as e:
                logger.error(f"Failed to parse LLM resume question JSON: {e}")

        # Intelligent Fallback Resume Question Generator
        if category == "intro":
            cand_name = resume_data.get("candidate_name", "Candidate")
            primary_tech = resume_data.get("primary_technology", "Software Engineering")
            return {
                "topic": "Candidate Introduction & Background",
                "category": "intro",
                "question": f"Welcome {cand_name}! Walk me through your background and what you’ve been focusing on recently in {primary_tech}.",
                "expected_answer": f"Candidate introduces themselves, highlights experience with {primary_tech}, and describes key technical projects.",
                "keywords": ["introduction", "background", primary_tech]
            }
        elif category == "intro_followup":
            skills_first = resume_data.get("skills", ["distributed systems"])[0]
            return {
                "topic": "Background Follow-up & Specialization",
                "category": "intro_followup",
                "question": f"You mentioned working heavily with {skills_first} and distributed pipelines—what drew you toward performance engineering and systems architecture over general application development?",
                "expected_answer": "Candidate articulates their motivation for performance engineering, systems architecture, and low-level optimization.",
                "keywords": [skills_first, "performance-engineering", "systems-architecture"]
            }
        elif category == "project" and projects:
            proj = projects[0]
            pname = proj.get("name", "Project")
            ptest = ", ".join(proj.get("tech_stack", ["Python"]))
            return {
                "topic": f"Project: {pname}",
                "category": "project",
                "question": f"In your project '{pname}', you used {ptest}. What was the most challenging technical feature you implemented, and how did you design its architecture?",
                "expected_answer": f"Clear explanation of architecture, technical choices, and trade-offs made during {pname}.",
                "keywords": [pname, "architecture", "trade-offs"]
            }
        elif category == "hr_behavioral":
            return {
                "topic": "Behavioral & Conflict Resolution",
                "category": "hr_behavioral",
                "question": "Can you describe a situation in one of your past projects where you encountered a critical technical blocker under tight deadlines? How did you resolve it?",
                "expected_answer": "STAR method explanation demonstrating problem-solving, communication, and resilience under pressure.",
                "keywords": ["problem-solving", "deadlines", "resilience"]
            }
        else:
            first_skill = resume_data.get("skills", ["Python"])[0]
            return {
                "topic": f"Skill: {first_skill}",
                "category": "skill",
                "question": f"You mentioned {first_skill} on your resume. How do you approach error handling, concurrency, and performance optimization when developing applications with {first_skill}?",
                "expected_answer": f"Explanation of best practices, error handling, and memory/performance considerations in {first_skill}.",
                "keywords": [first_skill, "best-practices", "performance"]
            }

    def generate_final_report(
        self,
        technology: str,
        answers_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        prompt = f"""
Act as a Principal Engineer and Hiring Manager. Analyze this candidate's complete interview history:

Technology Track: {technology}
Interview QA Data: {json.dumps(answers_history, indent=2)}

Generate a detailed final performance report STRICTLY in JSON format:
{{
  "technical_score": <float 0-10>,
  "communication_score": <float 0-10>,
  "confidence_rating": <float 0-10>,
  "strong_topics": ["<topic1>", "<topic2>"],
  "weak_topics": ["<topic1>", "<topic2>"],
  "overall_feedback": "<Comprehensive synthesis of strengths and areas of growth>",
  "learning_roadmap": [
    {{
      "topic": "<Weak Topic>",
      "action_item": "<Concrete study task or project exercise>",
      "recommended_resource": "<Documentation link or book suggestion>"
    }}
  ]
}}
"""
        raw_output = self._call_llm_for_task("analysis", prompt)
        if raw_output:
            try:
                return self._parse_json(raw_output)
            except Exception as e:
                logger.error(f"Failed to parse LLM final report JSON: {e}")

        # Fallback Mock Report
        total_score = sum(_safe_float(a.get("score"), 7.0) for a in answers_history)
        count = max(len(answers_history), 1)
        avg_tech = round(total_score / count, 1)
        
        return {
            "technical_score": avg_tech,
            "communication_score": 8.0,
            "confidence_rating": 8.2,
            "strong_topics": [f"{technology} Fundamentals", "Problem Solving"],
            "weak_topics": ["Edge cases", "Deep Internals"],
            "overall_feedback": f"Demonstrated solid proficiency in {technology}. Good structural thinking with minor gaps in deep architectural nuances.",
            "learning_roadmap": [
                {
                    "topic": f"{technology} Advanced Internals",
                    "action_item": "Review official language specifications and concurrency models.",
                    "recommended_resource": f"Official {technology} Documentation"
                }
            ]
        }
