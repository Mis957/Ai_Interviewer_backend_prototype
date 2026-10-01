import json
import logging
import re
import time
import requests
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

        # LM Studio Local AI Configuration
        self.lm_studio_base_url: str = getattr(settings, "LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        self.lm_studio_model: str = getattr(settings, "LM_STUDIO_MODEL", "meta-llama-3.1-8b-instruct")
        self.lm_studio_api_key: str = getattr(settings, "LM_STUDIO_API_KEY", "lm-studio")

        # Per-Task API Provider Chain Lists
        self.question_gen_providers: List[str] = [p.strip().lower() for p in getattr(settings, "QUESTION_GEN_PROVIDERS", "lm_studio,groq,gemini").split(",") if p.strip()]
        self.evaluation_providers: List[str] = [p.strip().lower() for p in getattr(settings, "EVALUATION_PROVIDERS", "lm_studio,groq,gemini").split(",") if p.strip()]
        self.analysis_providers: List[str] = [p.strip().lower() for p in getattr(settings, "ANALYSIS_PROVIDERS", "lm_studio,groq,gemini").split(",") if p.strip()]

        if self.api_key and not self.api_key.startswith("your-") and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Google GenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    def _call_lm_studio(
        self,
        prompt: str,
        system_prompt: str = "Act as an expert technical interviewer.",
        task_type: Optional[str] = None
    ) -> str:
        """Helper to invoke local LM Studio OpenAI-compatible endpoint."""
        url = f"{self.lm_studio_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.lm_studio_api_key}"
        }
        max_tok = 1500 if task_type in ("analysis", "evaluation") else 800
        payload = {
            "model": self.lm_studio_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tok
        }
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No choices returned from LM Studio.")
        content = choices[0].get("message", {}).get("content", "")
        return content.strip()

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
        provider_chain = providers_map.get(task_type, ["lm_studio", "groq", "gemini"])

        for provider in provider_chain:
            if provider in ("lm_studio", "lmstudio", "local"):
                try:
                    out = self._call_lm_studio(prompt, system_prompt, task_type=task_type)
                    if out:
                        logger.info(f"[{task_type}] Successfully fulfilled request via LM Studio ({self.lm_studio_model}).")
                        return out
                except Exception as e:
                    logger.warning(f"[{task_type}] LM Studio provider failed: {e}. Attempting fallback...")
            elif provider == "groq":
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
                if "parameters" in res and isinstance(res["parameters"], dict):
                    res = {**res["parameters"], **res}
                return res
        except Exception:
            pass

        # Attempt 2: Clean trailing commas and escape unescaped line breaks inside double-quoted string values
        try:
            # Remove trailing commas before closing braces or brackets
            cleaned = re.sub(r',\s*([}\]])', r'\1', text)
            fixed_text = re.sub(
                r'"([^"\\]|\\.)*"',
                lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'),
                cleaned,
                flags=re.DOTALL
            )
            res = json.loads(fixed_text, strict=False)
            if isinstance(res, dict):
                if "parameters" in res and isinstance(res["parameters"], dict):
                    res = {**res["parameters"], **res}
                return res
        except Exception:
            pass

        # Attempt 3: Field-level regex extraction for damaged LLM output
        # Case A: Question Generation
        q_match = re.search(r'"question"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
        if q_match:
            topic_match = re.search(r'"topic"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            ans_match = re.search(r'"expected_answer"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            return {
                "topic": topic_match.group(1) if topic_match else "Technical Concepts",
                "question": q_match.group(1),
                "expected_answer": ans_match.group(1) if ans_match else "Comprehensive technical explanation.",
                "keywords": []
            }

        # Case B: Evaluation output
        score_match = re.search(r'"score"\s*:\s*([\d\.]+)', text)
        if score_match:
            fb_match = re.search(r'"feedback"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            conf_match = re.search(r'"confidence_score"\s*:\s*([\d\.]+)', text)
            diff_match = re.search(r'"next_difficulty"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            fluency_match = re.search(r'"fluency_feedback"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            return {
                "score": float(score_match.group(1)),
                "confidence_score": float(conf_match.group(1)) if conf_match else 7.5,
                "feedback": fb_match.group(1) if fb_match else "Answer evaluated successfully.",
                "fluency_feedback": fluency_match.group(1) if fluency_match else "Clear verbal delivery.",
                "next_difficulty": diff_match.group(1) if diff_match else "Medium",
                "filler_words_detected": [],
                "missing_topics": []
            }

        # Case C: Final report output
        tech_score_match = re.search(r'"technical_score"\s*:\s*([\d\.]+)', text)
        if tech_score_match:
            comm_match = re.search(r'"communication_score"\s*:\s*([\d\.]+)', text)
            overall_fb_match = re.search(r'"overall_feedback"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            return {
                "technical_score": float(tech_score_match.group(1)),
                "communication_score": float(comm_match.group(1)) if comm_match else 8.0,
                "confidence_rating": 8.0,
                "strong_topics": [],
                "weak_topics": [],
                "overall_feedback": overall_fb_match.group(1) if overall_fb_match else "Good interview performance.",
                "learning_roadmap": []
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

Provide your evaluation STRICTLY in JSON format with NO markdown formatting, commentary, or tool calls:
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
        system_prompt = "You are an expert technical interviewer and speech fluency evaluator. Never output tool calls or markdown wrappers. Always output valid JSON strictly matching the requested schema."
        raw_output = self._call_llm_for_task("evaluation", prompt, system_prompt=system_prompt)
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
        if stage in ("intro", "stage1_intro"):
            stage_instruction = (
                f"STAGE 1 OPENING DIRECTIVE: You MUST ask the candidate to tell you about themselves and introduce their technical background. "
                f"Greet the candidate and ask: 'Could you tell me about yourself and walk me through your technical background and experience with {technology}?' "
                f"DO NOT ask about projects, specific code, or technical puzzles in this opening question. Strictly ask them to introduce themselves. Strictly 1-2 concise sentences."
            )
        elif stage in ("intro_followup", "stage1_intro_followup"):
            prev_top = previous_topic or technology
            stage_instruction = f"STAGE 1 FOLLOW-UP: Ask a concise, natural follow-up regarding their work with '{prev_top}' and what motivated them toward this domain. Strictly 1-2 sentences."
        elif stage in ("project", "stage2_project_deepdive"):
            vague_push = " Probe sharply for specific bottlenecks or performance profiling tools used." if (previous_score is not None and previous_score < 6.0) else ""
            stage_instruction = f"STAGE 2 PROJECT ARCHITECTURE: Ask a targeted question about an architectural challenge, bottleneck, concurrency issue, or engineering trade-off in a real-world project built with {technology}.{vague_push} Strictly 1-2 concise sentences."
        elif stage in ("technical_adaptive", "stage3_technical_fundamentals"):
            if adaptive_mode == "deep_dive" and previous_topic:
                stage_instruction = f"STAGE 3 DEEP-DIVE: The candidate showed good understanding of '{previous_topic}'. Drill down into internal mechanics, memory/performance trade-offs, or an edge case of '{previous_topic}'. Strictly 1-2 concise sentences."
            elif adaptive_mode == "pivot" and previous_topic:
                stage_instruction = f"STAGE 3 PIVOT: The candidate struggled on '{previous_topic}'. Pivot cleanly away to a foundational core concept in {technology} (e.g., if Python: functions, decorators, generators, or context managers). Strictly 1-2 concise sentences."
            else:
                stage_instruction = (
                    f"STAGE 3 TECHNICAL FUNDAMENTALS: Ask an on-point, precise technical question testing core concepts, internal mechanisms, or language features in {technology} at a {difficulty} level. "
                    f"For example, if {technology} is Python, ask about specific concepts like functions (first-class functions, args/kwargs, closures), decorators (wrapping, implementation, decorators with arguments), generators & iterators (yield, memory efficiency), the GIL and multithreading vs multiprocessing, context managers, asyncio/event loop, or OOP/dunder methods. "
                    f"Pick ONE specific concept directly. Topics already discussed (DO NOT REPEAT): {avoid_str}. Strictly 1-2 concise sentences."
                )

        prompt = f"""You are a senior technical interviewer conducting a live spoken voice interview for a {role_str} role ({yoe_str} experience).

Interview Context:
- Track: {technology}
- Target Difficulty: {difficulty}
- Stage Directive: {stage_instruction}
- Topics Already Discussed (DO NOT REPEAT): {avoid_str}

CRITICAL RULES FOR GENERATING THE QUESTION:
1. NATURAL SPOKEN VOICE: The question will be read aloud to the candidate via Text-to-Speech. Phrase it conversationally as a real interviewer speaking directly to the candidate using "you" (e.g., "Could you tell me about yourself...", "In your project, how did you handle...", "How do decorators work in Python...").
2. ON POINT, PRECISE & CONCISE: The question must be strictly 1 to 2 clear sentences maximum. No rambling, no introductory fluff ("Here is your next question:", "Great, moving on to..."), and no combined multiple questions.
3. CONVERSATIONAL TECHNICAL DISCUSSION: NEVER ask written exam problems or coding puzzle instructions (e.g. NEVER say "Write a function...", "Write a script...", or "Given an array..."). Ask conceptual, architectural, or mechanism-based questions that the candidate can explain verbally.
4. SINGLE FOCUSED TOPIC: Probe one clear concept or scenario.
5. NO TOOL CALLS: NEVER output function calls or tool calls. Do NOT output a JSON with 'name' or 'parameters'. Output strictly the JSON schema requested below.

Return STRICTLY in JSON format with NO markdown wrapping:
{{
  "topic": "<Specific Topic Name>",
  "question": "<Clean, direct, conversational spoken question (1-2 sentences)>",
  "expected_answer": "<Concise summary of key concepts/points expected in candidate's verbal response>",
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
        system_prompt = "You are a professional, senior technical interviewer conducting a live voice interview. You ask clean, concise, verbal questions that sound natural when spoken aloud. Never output tool calls. Always output valid JSON strictly matching the requested schema."
        raw_output = self._call_llm_for_task("question_gen", prompt, system_prompt=system_prompt)
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
                "question": f"Welcome! Could you tell me about yourself and walk me through your technical background and experience with {technology}?",
                "expected_answer": f"Candidate introduces themselves, highlights experience with {technology}, and describes recent technical focus.",
                "keywords": ["introduction", "background", technology]
            }
        elif stage in ("intro_followup", "stage1_intro_followup"):
            return {
                "topic": "Background Follow-up & Specialization",
                "question": f"You mentioned working with {technology}—what specifically drew you toward performance engineering and systems architecture?",
                "expected_answer": "Candidate articulates their motivation for performance engineering and systems architecture.",
                "keywords": [technology, "performance-engineering", "systems"]
            }
        elif stage in ("project", "stage2_project_deepdive"):
            return {
                "topic": f"{technology} Project Architecture",
                "question": f"In your past projects using {technology}, what was a significant architectural decision or performance bottleneck you had to solve?",
                "expected_answer": f"Explanation of real-world system architecture, design decisions, and bottlenecks in {technology}.",
                "keywords": [technology, "architecture", "bottlenecks"]
            }

        # Stage 3 Technical concepts fallback bank
        t_low = technology.lower()
        existing_str = " ".join(existing_topics or []).lower()
        if "python" in t_low:
            py_bank = [
                ("Functions & Argument Passing", "Could you explain how argument passing works in Python functions, specifically regarding mutable versus immutable default arguments?"),
                ("Decorators in Python", "How do decorators work under the hood in Python, and how would you implement a custom decorator that accepts arguments?"),
                ("Generators & Yield", "What is the difference between a generator and a standard function in Python, and how does the yield keyword optimize memory usage?"),
                ("GIL & Concurrency", "How does the Global Interpreter Lock (GIL) impact multithreading in Python, and when would you choose multiprocessing instead?"),
                ("Context Managers", "How do context managers work in Python using the 'with' statement, and what methods are required to implement one from scratch?"),
                ("OOP & Dunder Methods", "What is the difference between '__new__' and '__init__' in Python, and when would you override '__new__'?")
            ]
            for t_name, q_txt in py_bank:
                if t_name.lower() not in existing_str and q_txt[:30].lower() not in existing_str:
                    return {
                        "topic": t_name,
                        "question": q_txt,
                        "expected_answer": f"Detailed technical explanation of {t_name} in Python.",
                        "keywords": ["Python", t_name.lower()]
                    }

        return {
            "topic": f"{technology} Architecture & Best Practices",
            "question": f"How do you approach error handling and performance optimization when building {difficulty.lower()}-level applications in {technology}?",
            "expected_answer": f"Clear explanation of design patterns, error handling, memory management, and performance optimization in {technology}.",
            "keywords": [technology, "architecture", difficulty.lower(), "best-practices"]
        }

    def generate_resume_question(
        self,
        resume_data: Dict[str, Any],
        category: str,
        difficulty: str,
        existing_topics: Optional[List[str]] = None,
        target_project: Optional[Dict[str, Any]] = None,
        project_aspect: Optional[str] = None,
        target_technology: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates interview question specifically tailored to candidate's uploaded resume (3-Stage Flow):
        - Stage 1: intro ("Tell me about yourself")
        - Stage 2: project (Covering all resume projects up to max 5 questions with architecture, bottlenecks, and trade-offs)
        - Stage 3: technology/skill (Core concepts like functions, decorators, generators for mentioned technologies till timer ends)
        """
        avoid_str = ", ".join(existing_topics) if existing_topics else "None"
        candidate_name = resume_data.get("candidate_name", "Candidate")
        skills_str = ", ".join(resume_data.get("skills", ["Software Engineering"]))
        projects = resume_data.get("projects", [])
        proj_str = json.dumps(projects)
        hr_topics_str = ", ".join(resume_data.get("hr_topics", ["Teamwork", "Problem Solving"]))

        category_instructions = ""
        if category == "intro":
            category_instructions = (
                f"STAGE 1 OPENING DIRECTIVE: You MUST ask the candidate to tell you about themselves and introduce their technical background. "
                f"Greet candidate '{candidate_name}' warmly and ask: 'Could you tell me about yourself and walk me through your technical background and recent work?' "
                f"DO NOT ask technical exam questions or deep project questions here. Strictly ask them to introduce themselves. Strictly 1-2 concise sentences."
            )
        elif category == "intro_followup":
            category_instructions = f"STAGE 1 FOLLOW-UP: Follow up naturally on candidate '{candidate_name}'s background with {skills_str} and ask what motivated them to specialize in this field. Strictly 1-2 sentences."
        elif category == "project":
            if target_project:
                pname = target_project.get("name", "Project")
                ptech = ", ".join(target_project.get("tech_stack", [])) or "the core tech stack"
                pdesc = target_project.get("description", "")
                if project_aspect == "overview":
                    category_instructions = (
                        f"STAGE 2 PROJECT ARCHITECTURE DIRECTIVE: Focus specifically on the candidate's project '{pname}' (Tech Stack: {ptech}. Description: {pdesc}). "
                        f"Ask an on-point, precise question about the high-level architecture of '{pname}', their specific role, and how they structured the system. "
                        f"Strictly 1 to 2 concise sentences."
                    )
                elif project_aspect == "hurdle_or_bottleneck":
                    category_instructions = (
                        f"STAGE 2 PROJECT TECHNICAL CHALLENGE DIRECTIVE: Focus specifically on the candidate's project '{pname}' (Tech Stack: {ptech}). "
                        f"Ask an on-point, precise question about the most difficult technical hurdle, performance bottleneck, concurrency issue, or complex bug they tackled while building '{pname}' and how they resolved it. "
                        f"Strictly 1 to 2 concise sentences."
                    )
                elif project_aspect == "tradeoffs_or_scaling":
                    category_instructions = (
                        f"STAGE 2 PROJECT TRADE-OFFS & SCALING DIRECTIVE: Focus specifically on the candidate's project '{pname}' (Tech Stack: {ptech}). "
                        f"Ask an on-point, precise question about the engineering trade-offs they made (e.g., choice of {ptech}, data storage/schema design) or how they would architect the system to scale under heavy traffic. "
                        f"Strictly 1 to 2 concise sentences."
                    )
                else:
                    category_instructions = (
                        f"STAGE 2 PROJECT DEEP-DIVE DIRECTIVE: Focus specifically on the candidate's project '{pname}' (Tech Stack: {ptech}). "
                        f"Ask a direct, precise question exploring the architectural decisions, trade-offs, or implementation challenges of '{pname}'. "
                        f"Strictly 1 to 2 concise sentences."
                    )
            elif projects:
                category_instructions = (
                    f"STAGE 2 PROJECT DIRECTIVE: Inquire about the candidate's projects ({proj_str}). Ask a sharp, focused question on architectural decisions, trade-offs, or technical hurdles. Strictly 1-2 concise sentences."
                )
            else:
                category_instructions = "STAGE 2 PROJECT DIRECTIVE: Ask about a significant engineering project they built, focusing on architectural decisions and trade-offs. Strictly 1-2 concise sentences."
        elif category in ("technology", "skill"):
            target_tech = target_technology or resume_data.get("primary_technology") or (skills_str.split(",")[0].strip() if skills_str else "Python")
            category_instructions = (
                f"STAGE 3 TECHNOLOGY & CORE CONCEPTS DIRECTIVE: The candidate has '{target_tech}' listed in their skills. "
                f"Ask an on-point, precise, concise technical question testing their understanding of a specific core concept, mechanism, or internal in {target_tech} at a {difficulty} level. "
                f"IMPORTANT: Ask about concrete mechanisms or language features. For example: "
                f"- If {target_tech} is Python: ask about specific concepts like functions (first-class functions, args/kwargs, closures), decorators (function wrapping, custom decorators with arguments), generators & iterators (yield, memory management), the Global Interpreter Lock (GIL) and multithreading vs multiprocessing, context managers (__enter__/__exit__), asyncio/event loop, or object-oriented features (dunder methods, MRO). "
                f"- If {target_tech} is SQL/DBMS: ask about indexing (B-Tree, clustered vs non-clustered), ACID transactions & isolation levels, query execution plans, or normalization. "
                f"- If {target_tech} is another framework or tool: ask about its core mechanisms, lifecycle, concurrency, or performance trade-offs. "
                f"DO NOT ask broad or vague questions. Focus on ONE specific mechanism. "
                f"DO NOT repeat any topic already discussed: {avoid_str}. "
                f"Strictly 1 to 2 sentences. No coding on paper."
            )
        elif category == "hr_behavioral":
            category_instructions = "BEHAVIORAL: Ask a concise behavioral question about handling critical blockers, team conflicts, or tight deadlines under pressure. Strictly 1-2 sentences."
        else:
            category_instructions = f"Ask an on-point, precise interview question for {category} at {difficulty} level. Strictly 1-2 concise sentences."

        prompt = f"""You are a senior technical interviewer conducting a live voice interview for candidate '{candidate_name}' based on their uploaded resume.

Candidate Profile:
- Skills: {skills_str}
- Projects: {proj_str}
- Category: {category}
- Difficulty: {difficulty}
- Stage Directive: {category_instructions}
- Topics Already Discussed (DO NOT REPEAT): {avoid_str}

CRITICAL RULES FOR GENERATING THE QUESTION:
1. SPOKEN INTERVIEWER TONE: Speak directly to candidate '{candidate_name}' using "you" (e.g. "Could you tell me about yourself...", "In your project '{target_project.get('name', 'project') if target_project else 'project'}', how did you...", "How do decorators work in Python..."). Phrase the question naturally for text-to-speech voice delivery.
2. ON POINT, PRECISE & CONCISE: The question must be strictly 1 to 2 clear sentences. NO introductory fluff or conversational filler (e.g., NEVER say "Hello Oliver", "Great to meet you, today we will...", "Moving on to...", or "As we know..."). Get straight to the question.
3. CONVERSATIONAL VERBAL TECHNICAL DISCUSSION: Inquire about mechanisms, concepts, design decisions, and how things work under the hood. NEVER ask the candidate to write code or solve coding puzzles (NEVER say "Write a function...", "Write a script...", or "Given an array...").
4. ACCURATE TO STAGE DIRECTIVE: Strictly follow the stage directive above.
5. NO TOOL CALLS: Output strictly the JSON schema requested below with NO markdown formatting or commentary.

Return STRICTLY in JSON format:
{{
  "topic": "<Specific Topic or Concept Name>",
  "category": "{category}",
  "question": "<On point, precise, concise spoken question (strictly 1-2 sentences)>",
  "expected_answer": "<Concise summary of key technical points expected in candidate's verbal response>",
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
        system_prompt = "You are an experienced technical interviewer conducting a live verbal resume interview. You ask clean, direct, spoken questions that are on point, precise, and concise. Never output tool calls. Always output valid JSON strictly matching the requested schema."
        raw_output = self._call_llm_for_task("question_gen", prompt, system_prompt=system_prompt)
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
            return {
                "topic": "Candidate Introduction & Background",
                "category": "intro",
                "question": f"Welcome {candidate_name}! Could you tell me about yourself and walk me through your technical background and recent work?",
                "expected_answer": f"Candidate introduces themselves, highlights experience with {skills_str}, and describes key technical projects.",
                "keywords": ["introduction", "background", "experience"]
            }
        elif category == "intro_followup":
            skills_first = resume_data.get("skills", ["distributed systems"])[0]
            return {
                "topic": "Background Follow-up & Specialization",
                "category": "intro_followup",
                "question": f"You mentioned extensive work with {skills_first}—what specifically drew you toward this area over general application development?",
                "expected_answer": "Candidate articulates their motivation for performance engineering, systems architecture, and low-level optimization.",
                "keywords": [skills_first, "specialization", "architecture"]
            }
        elif category == "project":
            proj = target_project or (projects[0] if projects else {"name": "Software Project", "tech_stack": ["Python"]})
            pname = proj.get("name", "Project")
            ptech = ", ".join(proj.get("tech_stack", ["Python"])) or "the tech stack"
            if project_aspect == "overview":
                return {
                    "topic": f"Project Architecture: {pname}",
                    "category": "project",
                    "question": f"In your project '{pname}', could you walk me through the high-level architecture and your primary technical responsibilities?",
                    "expected_answer": f"Clear overview of {pname} system architecture, core components, and candidate's technical contributions.",
                    "keywords": [pname, "architecture", "responsibilities"]
                }
            elif project_aspect == "hurdle_or_bottleneck":
                return {
                    "topic": f"Technical Challenge: {pname}",
                    "category": "project",
                    "question": f"What was the most challenging technical hurdle or performance bottleneck you encountered while building '{pname}', and how did you resolve it?",
                    "expected_answer": f"Detailed description of technical hurdle in {pname} and engineering solution implemented.",
                    "keywords": [pname, "bottleneck", "problem-solving"]
                }
            elif project_aspect == "tradeoffs_or_scaling":
                return {
                    "topic": f"Trade-offs & Scalability: {pname}",
                    "category": "project",
                    "question": f"What key architectural trade-offs did you make when choosing {ptech} for '{pname}', and how would you scale the system to handle 10x the load?",
                    "expected_answer": f"Explanation of trade-offs, technology choices, and scaling strategies for {pname}.",
                    "keywords": [pname, "trade-offs", "scalability"]
                }
            else:
                return {
                    "topic": f"Project: {pname}",
                    "category": "project",
                    "question": f"In your project '{pname}', what architectural decisions did you make with {ptech} and what trade-offs did you consider?",
                    "expected_answer": f"Clear explanation of architecture and trade-offs in {pname}.",
                    "keywords": [pname, "architecture", "trade-offs"]
                }
        elif category == "hr_behavioral":
            return {
                "topic": "Behavioral & Conflict Resolution",
                "category": "hr_behavioral",
                "question": "Can you describe a situation where you encountered a critical technical blocker under tight deadlines, and how you resolved it?",
                "expected_answer": "STAR method explanation demonstrating problem-solving, communication, and resilience under pressure.",
                "keywords": ["problem-solving", "deadlines", "resilience"]
            }
        else:
            # category in ("technology", "skill")
            target_tech = target_technology or resume_data.get("primary_technology") or (skills_str.split(",")[0].strip() if skills_str else "Python")
            t_low = target_tech.lower()
            existing_str = " ".join(existing_topics or []).lower()

            if "python" in t_low:
                python_bank = [
                    ("Decorators in Python", "How do decorators work under the hood in Python, and how would you implement a custom decorator that accepts arguments?"),
                    ("Functions & Argument Passing", "Could you explain how argument passing works in Python functions, specifically regarding mutable versus immutable default arguments?"),
                    ("Generators & Yield", "What is the difference between a generator and a standard function in Python, and how does the yield keyword optimize memory usage?"),
                    ("GIL & Concurrency", "How does the Global Interpreter Lock (GIL) impact multithreading in Python, and when would you choose multiprocessing instead?"),
                    ("Context Managers", "How do context managers work in Python using the 'with' statement, and what methods are required to implement one from scratch?"),
                    ("OOP & Dunder Methods", "What is the difference between '__new__' and '__init__' in Python, and when would you override '__new__'?")
                ]
                for topic_name, q_text in python_bank:
                    if topic_name.lower() not in existing_str and q_text[:30].lower() not in existing_str:
                        return {
                            "topic": topic_name,
                            "category": "technology",
                            "question": q_text,
                            "expected_answer": f"Comprehensive explanation of {topic_name} in Python.",
                            "keywords": ["Python", topic_name.lower()]
                        }
                return {
                    "topic": "Python Memory Management",
                    "category": "technology",
                    "question": "How does Python handle memory management and garbage collection with reference counting and cyclic references?",
                    "expected_answer": "Explanation of reference counting, garbage collection thresholds, and cyclic references in Python.",
                    "keywords": ["Python", "memory", "garbage-collection"]
                }
            elif "sql" in t_low or "dbms" in t_low or "database" in t_low:
                sql_bank = [
                    ("Database Indexing", "What is the difference between a clustered and non-clustered index in SQL, and when might an index hurt query performance?"),
                    ("ACID & Isolation Levels", "Could you explain the four ACID properties in relational databases, focusing on how isolation levels prevent dirty reads?"),
                    ("Query Optimization & Joins", "How do database query engines optimize INNER JOIN versus LEFT JOIN, and what role does an execution plan play?"),
                    ("Transactions & Concurrency", "What is the difference between optimistic and pessimistic locking in database transaction management?")
                ]
                for topic_name, q_text in sql_bank:
                    if topic_name.lower() not in existing_str:
                        return {
                            "topic": topic_name,
                            "category": "technology",
                            "question": q_text,
                            "expected_answer": f"Technical breakdown of {topic_name}.",
                            "keywords": [target_tech, topic_name.lower()]
                        }
            # Fallback for any other technology
            return {
                "topic": f"{target_tech} Core Concepts",
                "category": "technology",
                "question": f"How do you manage error handling, concurrency, and performance optimization when developing applications with {target_tech}?",
                "expected_answer": f"Best practices for concurrency, error handling, and performance in {target_tech}.",
                "keywords": [target_tech, "performance", "best-practices"]
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
        system_prompt = "You are a Principal Engineer and Hiring Manager. Always output valid JSON strictly matching the requested schema. Never output tool calls or markdown wrappers."
        raw_output = self._call_llm_for_task("analysis", prompt, system_prompt=system_prompt)
        if raw_output:
            try:
                data = self._parse_json(raw_output)
                if isinstance(data, dict) and any(k in data for k in ("technical_score", "overall_feedback", "strong_topics")):
                    return data
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
