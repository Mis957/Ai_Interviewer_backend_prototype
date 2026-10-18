import json
import logging
import re
import secrets
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

_QUESTION_FOCUSES = (
    ("core_concept", "Test one core concept or mechanism with a clear, concrete example."),
    ("debugging", "Present a realistic bug or unexpected behavior and ask how the candidate would investigate its cause."),
    ("performance", "Present a realistic performance symptom and ask which specific bottleneck or measurement they would investigate first."),
    ("concurrency_reliability", "Ask about one concurrency, failure-handling, or reliability scenario relevant to the technology."),
    ("trade_off", "Ask the candidate to explain one concrete technical choice and the consequence that mattered most."),
)

_PYTHON_QUESTION_PROGRESSION = (
    (
        "foundation",
        "Start with Python fundamentals such as built-in data types, mutability, function arguments, or scope. "
        "Ask about one basic behavior in a simple example.",
    ),
    (
        "object_oriented",
        "Ask about a core object-oriented concept in Python, such as classes versus instances, inheritance, "
        "or composition, using a simple practical example.",
    ),
    (
        "common_language_feature",
        "Ask about one commonly used Python feature, such as decorators, generators, iterators, or context managers, "
        "and its practical purpose.",
    ),
    (
        "practical_debugging",
        "Present a realistic Python bug, exception, or test behavior and ask how the candidate would reason about it.",
    ),
    (
        "advanced_internals",
        "Ask about one advanced Python topic such as async execution, the GIL, memory behavior, or performance, "
        "grounded in a concrete scenario.",
    ),
)


def _question_focus(sequence: int) -> tuple[str, str]:
    return _QUESTION_FOCUSES[sequence % len(_QUESTION_FOCUSES)]


def _technology_progression(technology: str, sequence: int) -> tuple[str, str]:
    normalized_technology = technology.casefold()
    progression = _PYTHON_QUESTION_PROGRESSION if "python" in normalized_technology else (
        ("foundation", f"Ask about a fundamental building block or basic usage of {technology}, grounded in a simple example."),
        ("core_model", f"Ask about a core programming, data, or object model concept relevant to {technology}."),
        ("common_feature", f"Ask about a commonly used feature or mechanism in {technology} and when it is useful."),
        ("practical_debugging", f"Present a realistic bug or unexpected behavior involving {technology} and ask how to investigate it."),
        ("advanced_application", f"Ask about one advanced mechanism, performance concern, or reliability scenario involving {technology}."),
    )
    return progression[min(max(sequence, 0), len(progression) - 1)]


def _choose_unused_question(
    questions: List[str], existing_topics: Optional[List[str]]
) -> str:
    existing_text = " ".join(existing_topics or []).casefold()
    unused_questions = [
        question for question in questions
        if question.casefold() not in existing_text
    ]
    return secrets.choice(unused_questions or questions)


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
        response = requests.post(url, json=payload, headers=headers, timeout=(2.5, 120))
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
        previous_score: Optional[float] = None,
        question_sequence: int = 0
    ) -> Dict[str, Any]:
        avoid_str = ", ".join(existing_topics) if existing_topics else "None"
        role_str = target_role or "Software Developer"
        yoe_str = years_of_experience or "1-3 years"

        stage_instruction = ""
        if stage in ("intro", "stage1_intro"):
            stage_instruction = (
                f"STAGE 1 OPENING: Ask the candidate to introduce themselves and summarize their technical background, including their experience with {technology}. "
                f"Use a warm, natural interviewer tone without a greeting or extra preamble. Do not ask about projects or technical puzzles."
            )
        elif stage in ("intro_followup", "stage1_intro_followup"):
            prev_top = previous_topic or technology
            stage_instruction = f"STAGE 1 FOLLOW-UP: Ask one natural follow-up grounded in their experience with '{prev_top}', focused on one specific detail or motivation."
        elif stage in ("project", "stage2_project_deepdive"):
            stage_instruction = (
                f"STAGE 2 PROJECT EXPERIENCE: The candidate supplied the technology track '{technology}', but no project details. "
                f"Invite them to discuss one project where they used {technology}, without assuming or inventing project details. "
                "Ask about one specific aspect only; do not append a second, unrelated system or scenario."
            )
        elif stage in ("technical_adaptive", "stage3_technical_fundamentals"):
            if adaptive_mode == "deep_dive" and previous_topic:
                stage_instruction = f"STAGE 3 DEEP-DIVE: The candidate showed good understanding of '{previous_topic}'. Ask one focused follow-up about a specific internal mechanism, edge case, or performance trade-off related to it."
            elif adaptive_mode == "pivot" and previous_topic:
                stage_instruction = f"STAGE 3 PIVOT: The candidate struggled on '{previous_topic}'. Switch to one foundational concept in {technology} and ask a clear, approachable question about it."
            else:
                focus_name, focus_guidance = _question_focus(question_sequence)
                stage_instruction = (
                    f"STAGE 3 TECHNICAL {focus_name.upper()}: {focus_guidance} "
                    f"Use {technology}, calibrate depth to {difficulty}, and ground it in one brief practical context. "
                    f"Do not repeat these topics: {avoid_str}."
                )

        prompt = f"""You are a senior technical interviewer conducting a live spoken voice interview for a {role_str} role ({yoe_str} experience).

Interview Context:
- Track: {technology}
- Target Difficulty: {difficulty}
- Candidate experience: {yoe_str}; calibrate depth to this level.
- Stage Directive: {stage_instruction}
- Topics Already Discussed (DO NOT REPEAT): {avoid_str}

CRITICAL RULES FOR GENERATING THE QUESTION:
1. SOUND LIKE A REAL INTERVIEWER: Address the candidate directly in natural spoken English. Use a brief, relevant setup so the candidate knows what situation or concept you mean; avoid generic prompts that could apply to anything.
2. BE SPECIFIC BUT TO THE POINT: Ask about one clearly named concept, decision, or scenario. Include only enough context to make the question meaningful, then ask one direct question. Keep it to 1-2 short sentences and end with a question mark.
3. ASK ONE THING: Ask one clear question, not a checklist. Avoid stacking asks with "and"; do not request several examples, comparisons, or solutions at once.
4. KEEP IT SPOKEN: Avoid written exam problems and coding-puzzle instructions such as "Write a function" or "Given an array." Ask something the candidate can answer aloud.
5. AVOID FILLER: Do not add greetings, transitions, praise, or phrases like "Here is your next question" or "Great, moving on."
6. VARY THE INTERVIEW: Follow the stage's requested angle. Do not turn every question into architecture or system design. Prefer concrete engineering work, language/framework behavior, debugging, performance, reliability, and trade-offs where relevant.
7. NO TOOL CALLS: NEVER output function calls or tool calls. Do NOT output a JSON with 'name' or 'parameters'. Output strictly the JSON schema requested below.
8. STAY ON SCOPE: Treat the selected Track and Stage Directive as the only subject. Do not invent a project, product, service, metric, or named system the candidate did not provide. In project stage, invite the candidate to supply their own example, but do not combine it with an unrelated scenario (for example, do not pair RAG project experience with API traffic-light monitoring). Ask about one topic and one thing only; avoid joining separate asks with "and".

Return STRICTLY in JSON format with NO markdown wrapping:
{{
  "topic": "<Specific Topic Name>",
  "question": "<Specific, natural spoken interview question with brief context and one focused ask (1-2 short sentences)>",
  "expected_answer": "<Concise summary of key concepts/points expected in candidate's verbal response>",
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
        system_prompt = "You are a thoughtful senior technical interviewer. Stay strictly within the supplied track and stage, never invent candidate project details or unrelated scenarios, and ask one concise, natural spoken question about one topic. Always output valid JSON strictly matching the requested schema."
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
                "topic": f"{technology} Project Experience",
                "question": f"If you have used {technology} in a project, what was one technical decision you made about it?",
                "expected_answer": f"A specific technical decision related to {technology} and the candidate's reasoning.",
                "keywords": [technology, "project", "technical-decision"]
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
            "topic": f"{technology} Core Concepts",
            "question": f"What is one core concept in {technology} that you consider essential?",
            "expected_answer": f"A clear explanation of one core concept in {technology}.",
            "keywords": [technology, "core-concept", difficulty.lower()]
        }

    def generate_resume_question(
        self,
        resume_data: Dict[str, Any],
        category: str,
        difficulty: str,
        existing_topics: Optional[List[str]] = None,
        target_project: Optional[Dict[str, Any]] = None,
        project_aspect: Optional[str] = None,
        target_technology: Optional[str] = None,
        last_score: Optional[float] = None,
        question_sequence: int = 0
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

        if last_score is None:
            score_guidance = "This is the first question; establish a clear baseline at the requested difficulty."
        elif last_score < 5.0:
            score_guidance = (
                f"The previous answer scored {last_score:.1f}/10. Make the next question easier and more foundational; "
                "if appropriate, clarify the same broad area without repeating the exact question."
            )
        elif last_score >= 8.0:
            score_guidance = (
                f"The previous answer scored {last_score:.1f}/10. Increase the challenge and ask a deeper follow-up "
                "or test a more advanced aspect of the next topic."
            )
        else:
            score_guidance = (
                f"The previous answer scored {last_score:.1f}/10. Keep the next question at a moderate level and "
                "build on the candidate's demonstrated knowledge."
            )

        if category == "intro":
            variation_focus = secrets.choice((
                "career direction and the candidate's path into this field",
                "the technical strength the candidate is most confident using",
                "how the candidate's experience connects to the target role",
                "a recent learning experience that shaped the candidate's interests",
            ))
        elif category == "project":
            project_variations = {
                "overview": (
                    "one feature's user-facing behavior",
                    "how information moves through one part of the project",
                    "the candidate's personal ownership of one component",
                    "one integration between technologies named for the project",
                ),
                "hurdle_or_bottleneck": (
                    "the evidence used to narrow down a bug",
                    "an edge case that caused unexpected behavior",
                    "how the candidate isolated a failure between components",
                    "a test or debugging technique used to verify a fix",
                ),
                "tradeoffs_or_scaling": (
                    "a trade-off between simplicity and flexibility",
                    "the effect of one implementation choice on maintainability",
                    "a decision about data storage or access, if relevant to the project",
                    "how the candidate knew an improvement was successful",
                ),
            }
            variation_focus = secrets.choice(project_variations.get(
                project_aspect,
                ("one implementation detail", "one debugging decision", "one technical trade-off"),
            ))
        elif category in ("technology", "skill"):
            target_tech = target_technology or resume_data.get("primary_technology") or "the listed technology"
            progression_stage, _ = _technology_progression(target_tech, question_sequence)
            technology_variations = {
                "foundation": (
                    "a basic data type or value behavior",
                    "function arguments, defaults, or scope",
                    "a simple operation and its result",
                ),
                "object_oriented": (
                    "how a class differs from an instance",
                    "inheritance versus composition",
                    "how an object encapsulates state and behavior",
                ),
                "common_language_feature": (
                    "a decorator or equivalent reusable behavior",
                    "lazy iteration or streaming values",
                    "resource management or cleanup",
                ),
                "practical_debugging": (
                    "how to isolate a failing test",
                    "how to trace an unexpected value",
                    "how to narrow an exception to its source",
                ),
                "advanced_internals": (
                    "asynchronous execution and where it helps",
                    "concurrency limits and how to work around them",
                    "memory use under a realistic workload",
                ),
                "core_model": (
                    "the technology's core data or object model",
                    "how state or data is represented",
                    "a fundamental operation and its behavior",
                ),
                "common_feature": (
                    "a commonly used feature and its practical purpose",
                    "a feature's effect on application behavior",
                    "choosing the right built-in mechanism for a task",
                ),
                "advanced_application": (
                    "a performance bottleneck and how to measure it",
                    "a reliability failure and how to contain it",
                    "an advanced mechanism and its trade-off",
                ),
            }
            variation_focus = secrets.choice(technology_variations.get(
                progression_stage,
                (
                    f"a core {target_tech} concept",
                    f"debugging a realistic {target_tech} issue",
                    f"a performance or reliability trade-off in {target_tech}",
                ),
            ))
        else:
            variation_focus = "a distinct example grounded in the candidate's background"

        if category == "intro":
            question_approach = secrets.choice((
                "open with a short invitation to reflect on the candidate's career path",
                "start with the candidate's strongest relevant technical skill",
                "ask how the candidate's background connects to their target role",
            ))
        elif category == "project" and project_aspect == "overview":
            question_approach = secrets.choice((
                "begin with the user or system outcome, then ask about the candidate's specific contribution",
                "start with one component's data flow and ask about the candidate's implementation choice",
                "ask what the candidate personally owned, without using a generic 'walk me through your project' opener",
            ))
        elif category == "project" and project_aspect == "hurdle_or_bottleneck":
            question_approach = secrets.choice((
                "present the challenge through the evidence used to diagnose it",
                "start with the unexpected behavior and ask for the first debugging step",
                "focus on the prevention or verification method rather than asking for a general project summary",
            ))
        elif category == "project":
            question_approach = secrets.choice((
                "frame the question around the consequence of one engineering trade-off",
                "ask how the candidate measured the impact of one implementation change",
                "explore why one option was chosen over an alternative",
            ))
        elif category in ("technology", "skill"):
            question_approach = secrets.choice((
                "use a brief, concrete example and ask the candidate to explain the underlying behavior",
                "describe a realistic symptom and ask what mechanism could cause it",
                "frame the concept as a choice between two approaches and ask for the deciding trade-off",
                "ask the candidate to predict what happens in a small scenario before explaining why",
            ))
        else:
            question_approach = "use a fresh, specific framing instead of a generic interview opener"

        category_instructions = ""
        if category == "intro":
            category_instructions = (
                "STAGE 1 OPENING: Invite the candidate to introduce themselves and summarize their technical background, "
                f"including experience relevant to the role. Focus on {variation_focus}; {question_approach}. "
                "Do not ask about projects or technical puzzles."
            )
        elif category == "intro_followup":
            category_instructions = f"STAGE 1 FOLLOW-UP: Ask one natural follow-up about the candidate's experience with {skills_str}, focusing on what motivated their interest in this area."
        elif category == "project":
            if target_project:
                pname = target_project.get("name", "Project")
                ptech = ", ".join(target_project.get("tech_stack", [])) or "the core tech stack"
                pdesc = target_project.get("description", "")
                if project_aspect == "overview":
                    category_instructions = (
                        f"STAGE 2 PROJECT EXPERIENCE: Use the candidate's project '{pname}' (Tech Stack: {ptech}. Description: {pdesc}) as context. "
                        f"Ask about {variation_focus} as one concrete contribution; {question_approach}. Avoid defaulting to architecture."
                    )
                elif project_aspect == "hurdle_or_bottleneck":
                    category_instructions = (
                        f"STAGE 2 PROJECT CHALLENGE: Focus on the candidate's project '{pname}' (Tech Stack: {ptech}. Description: {pdesc}). "
                        f"Ask about {variation_focus} as one specific project challenge and how they investigated it; {question_approach}."
                    )
                elif project_aspect == "tradeoffs_or_scaling":
                    category_instructions = (
                        f"STAGE 2 PROJECT IMPACT: Focus on the candidate's project '{pname}' (Tech Stack: {ptech}. Description: {pdesc}). "
                        f"Ask about {variation_focus} as one technical decision or improvement and its impact; {question_approach}. Do not add a separate scaling question."
                    )
                else:
                    category_instructions = (
                        f"STAGE 2 PROJECT DEEP-DIVE: Focus on the candidate's project '{pname}' (Tech Stack: {ptech}). "
                        f"Ask about {variation_focus} as one specific design decision or implementation challenge; {question_approach}."
                    )
            elif projects:
                category_instructions = (
                    f"STAGE 2 PROJECT: Use the candidate's projects ({proj_str}) as context. Ask about one specific implementation contribution or technical challenge, not broad architecture."
                )
            else:
                category_instructions = "STAGE 2 PROJECT: Ask about one specific feature they built or technical challenge they handled in an engineering project."
            category_instructions += f" Adapt the depth to the latest answer score: {score_guidance}"
        elif category in ("technology", "skill"):
            target_tech = target_technology or resume_data.get("primary_technology") or (skills_str.split(",")[0].strip() if skills_str else "Python")
            progression_stage, progression_guidance = (
                _technology_progression(target_tech, question_sequence)
            )
            category_instructions = (
                f"STAGE 3 TECH-STACK QUESTION - {progression_stage.upper()}: "
                f"The candidate lists '{target_tech}' as a skill. {progression_guidance} "
                f"Vary this run by focusing specifically on {variation_focus}; {question_approach}. "
                f"This is question {question_sequence + 1} for this technology. "
                f"Choose one specific concept or realistic situation and do not repeat these topics: {avoid_str}. "
                f"Do not assume expertise beyond the listed skill. Score adaptation: {score_guidance}"
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
- Latest answer score: {f"{last_score:.1f}/10" if last_score is not None else "No previous answer"}
- Use the latest score to choose the next question's depth: {score_guidance}
- Stage Directive: {category_instructions}
- Topics Already Discussed (DO NOT REPEAT): {avoid_str}

CRITICAL RULES FOR GENERATING THE QUESTION:
1. SPOKEN INTERVIEWER TONE: Speak directly to the candidate in natural conversational English suitable for text-to-speech. Avoid canned openings and over-formal phrasing.
2. SPECIFIC WITH CONTEXT: Ground the question in the named project, technology, or a plausible scenario. Ask about one concrete concept, decision, or challenge, not broad architecture by default.
3. ONE FOCUSED ASK: Ask one direct question, not a checklist or multiple requests joined with "and". Keep it to 1-2 short sentences and end with a question mark.
4. CONVERSATIONAL TECHNICAL DISCUSSION: Ask about concepts, mechanisms, design decisions, debugging, or experience that can be explained verbally. Never ask the candidate to write code or solve a coding puzzle.
5. ACCURATE TO STAGE DIRECTIVE: Follow the stage directive and do not invent candidate or project details that are absent from the resume.
6. STRONG NOVELTY: Do not repeat or lightly paraphrase a previous question. Each new question must target a meaningfully different concept, project detail, or reasoning angle from every item in Topics Already Discussed. Do not reuse their central subject even if you change the wording. Follow the supplied variation focus and interviewer approach for this run. Avoid generic repeated openings such as "Can you describe..." or "Walk me through..."; vary sentence structure and begin with the specific situation, decision, or concept.
7. VARY THE INTERVIEW: Across questions, vary between implementation, technical fundamentals, debugging, performance, reliability, and trade-offs instead of repeatedly asking architecture questions.
8. NO FILLER OR TOOL CALLS: Do not add greetings, transitions, praise, markdown, commentary, or tool calls. Output only the requested JSON.

Return STRICTLY in JSON format:
{{
  "topic": "<Specific Topic or Concept Name>",
  "category": "{category}",
  "question": "<Specific natural spoken interview question with brief context and one focused ask (1-2 short sentences)>",
  "expected_answer": "<Concise summary of key technical points expected in candidate's verbal response>",
  "keywords": ["<keyword1>", "<keyword2>"]
}}
"""
        system_prompt = "You are a thoughtful experienced interviewer conducting a live verbal resume interview. Make every question meaningfully different from all previously discussed questions, follow the supplied variation focus, stay grounded in the resume, and ask one concise, natural question. Always output valid JSON strictly matching the requested schema."
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
            intro_question = _choose_unused_question([
                f"Could you introduce yourself by describing your path into software engineering?",
                f"What part of your technical background best prepares you for the role you are targeting?",
                f"What is one technical area you have enjoyed developing recently?",
            ], existing_topics)
            return {
                "topic": "Candidate Introduction & Background",
                "category": "intro",
                "question": intro_question,
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
                project_question = _choose_unused_question([
                    f"What is one feature you implemented for '{pname}'?",
                    f"How did one part of '{pname}' use its listed technology stack?",
                    f"What component of '{pname}' did you personally own?",
                ], existing_topics)
                return {
                    "topic": f"Project Contribution: {pname}",
                    "category": "project",
                    "question": project_question,
                    "expected_answer": f"A specific contribution to {pname} and an explanation appropriate to the candidate's demonstrated level.",
                    "keywords": [pname, "implementation", "contribution"]
                }
            elif project_aspect == "hurdle_or_bottleneck":
                project_question = _choose_unused_question([
                    f"What was one technical issue you encountered while building '{pname}'?",
                    f"What evidence helped you find the cause of a bug in '{pname}'?",
                    f"Which edge case required you to change your implementation in '{pname}'?",
                ], existing_topics)
                return {
                    "topic": f"Technical Challenge: {pname}",
                    "category": "project",
                    "question": project_question,
                    "expected_answer": f"A relevant technical challenge in {pname} explained at a level appropriate to the candidate's demonstrated knowledge.",
                    "keywords": [pname, "technical-challenge", "problem-solving"]
                }
            elif project_aspect == "tradeoffs_or_scaling":
                project_question = _choose_unused_question([
                    f"What was one technical choice you made for '{pname}'?",
                    f"What trade-off mattered most in a decision you made for '{pname}'?",
                    f"How did you determine whether an improvement to '{pname}' was successful?",
                ], existing_topics)
                return {
                    "topic": f"Project Technical Decision: {pname}",
                    "category": "project",
                    "question": project_question,
                    "expected_answer": f"A concrete technical choice for {pname} and its impact, if appropriate to the candidate's demonstrated level.",
                    "keywords": [pname, ptech, "technical-decision"]
                }
            else:
                return {
                    "topic": f"Project: {pname}",
                    "category": "project",
                    "question": f"What is one technical contribution you made to '{pname}'?",
                    "expected_answer": f"A specific technical contribution to {pname}.",
                    "keywords": [pname, "technical-contribution"]
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
                    ("Python Fundamentals", [
                        "In Python, how does mutability affect what happens when two variables refer to the same list?",
                        "Why can a mutable default argument cause surprising behavior across Python function calls?",
                        "How does Python determine whether a variable is local or global inside a function?",
                    ]),
                    ("Object-Oriented Programming", [
                        "In Python, what is the difference between a class and an instance?",
                        "When would composition be a better choice than inheritance in Python?",
                        "How does an instance get access to methods defined on its Python class?",
                    ]),
                    ("Decorators in Python", [
                        "In Python, what does a decorator do to a function, and when might you use one?",
                        "How can a Python decorator add behavior without changing the decorated function's body?",
                        "What role does a wrapper function play in a Python decorator?",
                    ]),
                    ("Generators & Yield", [
                        "How does the yield keyword let a Python function produce values lazily?",
                        "When is a Python generator more memory-efficient than building a list?",
                    ]),
                    ("GIL & Concurrency", [
                        "When might the Global Interpreter Lock affect a CPU-bound Python application?",
                        "Why might adding Python threads fail to speed up CPU-heavy work?",
                    ]),
                    ("Context Managers", [
                        "What problem does a context manager solve when working with files in Python?",
                        "How does a Python with statement help ensure a resource is cleaned up?",
                    ]),
                    ("Python Memory Management", [
                        "How does Python reclaim memory when objects are no longer in use?",
                        "Why does Python need garbage collection in addition to reference counting?",
                    ])
                ]
                if last_score is not None and last_score < 5.0:
                    bank_start = 0
                else:
                    bank_start = min(question_sequence, len(python_bank) - 1)
                ordered_bank = python_bank[bank_start:] + python_bank[:bank_start]
                for topic_name, question_options in ordered_bank:
                    unused_questions = [
                        question for question in question_options
                        if question.casefold() not in existing_str
                    ]
                    if unused_questions:
                        q_text = secrets.choice(unused_questions)
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
            elif any(
                database_term in t_low
                for database_term in ("sql", "dbms", "database", "postgres", "mysql", "sqlite", "mariadb")
            ):
                sql_bank = [
                    ("SQL Fundamentals", [
                        "How would you use a WHERE clause to filter rows in a SQL query?",
                        "What is the difference between filtering rows with WHERE and filtering groups with HAVING?",
                    ]),
                    ("SQL Joins", [
                        "When would you use a LEFT JOIN instead of an INNER JOIN?",
                        "Why can a join produce more rows than either of its input tables?",
                    ]),
                    ("Database Indexing", [
                        "How does an index help a SQL query that filters a large table?",
                        "What is one trade-off of adding an index to a frequently updated table?",
                    ]),
                    ("Transactions", [
                        "What problem do transactions solve when an operation updates several related rows?",
                        "Why should related database updates succeed or fail as one transaction?",
                    ]),
                    ("Transaction Isolation", [
                        "How can transaction isolation prevent a query from reading another transaction's incomplete changes?",
                        "What kind of inconsistent result can occur when concurrent transactions are not isolated?",
                    ])
                ]
                bank_start = secrets.randbelow(len(sql_bank))
                ordered_sql_bank = sql_bank[bank_start:] + sql_bank[:bank_start]
                for topic_name, question_options in ordered_sql_bank:
                    unused_questions = [
                        question for question in question_options
                        if question.casefold() not in existing_str
                    ]
                    if unused_questions:
                        q_text = secrets.choice(unused_questions)
                        return {
                            "topic": topic_name,
                            "category": "technology",
                            "question": q_text,
                            "expected_answer": f"Technical breakdown of {topic_name}.",
                            "keywords": [target_tech, topic_name.lower()]
                        }
            progression_stage, _ = _technology_progression(target_tech, question_sequence)
            progression_difficulty = difficulty
            fallback_questions = (
                (
                    f"What problem does {target_tech} solve in an application?",
                    f"Where would you choose {target_tech} over a simpler alternative?",
                    f"What role can {target_tech} play in a typical application?",
                ),
                (
                    f"What is one important building block of {target_tech}, and what does it do?",
                    f"How does {target_tech} represent or process its core data?",
                    f"What basic operation would you expect any user of {target_tech} to understand?",
                ),
                (
                    f"How would you use a common {target_tech} feature in a typical task?",
                    f"What kind of task is a built-in {target_tech} feature especially useful for?",
                    f"When would you reach for a standard {target_tech} mechanism rather than custom code?",
                ),
                (
                    f"If something behaved unexpectedly in {target_tech}, what would you check first?",
                    f"What evidence would help you trace a bug in a {target_tech} application?",
                    f"How would you narrow down which part of a {target_tech} workflow caused a failure?",
                ),
                (
                    f"What advanced behavior or limitation of {target_tech} matters in a high-load application?",
                    f"What {target_tech} performance bottleneck would you measure before trying to optimize?",
                    f"What reliability trade-off should an experienced {target_tech} developer consider?",
                ),
            )
            fallback_stage = min(max(question_sequence, 0), len(fallback_questions) - 1)
            return {
                "topic": f"{target_tech} {progression_stage.replace('_', ' ').title()}",
                "category": "technology",
                "question": _choose_unused_question(
                    list(fallback_questions[fallback_stage]), existing_topics
                ),
                "expected_answer": f"A clear {progression_difficulty.lower()}-level explanation relevant to {target_tech}.",
                "keywords": [target_tech, progression_stage]
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
