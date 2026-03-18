import json
import logging
import os
from typing import Any, Dict, List, Tuple

import requests

from utils import (
    clean_text,
    coerce_quiz_structure,
    coerce_slides_structure,
    ensure_teaching_flow,
    extract_key_lines,
    extract_topic_name,
    heuristic_quiz,
    parse_json_response,
    prepare_text_for_llm,
)

logger = logging.getLogger(__name__)


class InvalidLLMResponseError(RuntimeError):
    pass


def build_slide_prompt(input_text: str, level: str, density: str) -> str:
    return f"""Convert the following notes into presentation slides.

Rules:
- Each slide must have a title
- Use concise bullet points (no paragraphs)
- Maintain logical teaching flow:
  Introduction → Concepts → Example → Summary
- Detect processes and create a process slide if needed
- Adjust explanation level based on difficulty: {level}
- Adjust number of bullets based on density: {density}

Return ONLY valid JSON:
[
  {{
    "title": "...",
    "points": ["...", "..."]
  }}
]

Notes:
{input_text}
"""


def build_quiz_prompt(slides: List[Dict[str, Any]], level: str) -> str:
    serialized_slides = json.dumps(slides, ensure_ascii=False, indent=2)
    return f"""Create 3 multiple-choice questions from the following slide content.

Rules:
- Each question must have exactly 4 options
- Keep the language suitable for difficulty: {level}
- The answer must exactly match one of the options
- Return ONLY valid JSON:
[
  {{
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "answer": "..."
  }}
]

Slides:
{serialized_slides}
"""


def get_provider_name() -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("HUGGINGFACE_API_KEY"):
        return "huggingface"
    return "fallback"


def is_llm_configured() -> bool:
    return get_provider_name() != "fallback"


def call_llm(prompt: str, temperature: float = 0.3) -> str:
    provider = get_provider_name()
    if provider == "openai":
        return _call_openai(prompt, temperature)
    if provider == "gemini":
        return _call_gemini(prompt)
    if provider == "huggingface":
        return _call_huggingface(prompt)
    raise RuntimeError("No LLM provider is configured. Set OPENAI_API_KEY, GEMINI_API_KEY, or HUGGINGFACE_API_KEY.")


def _call_openai(prompt: str, temperature: float) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": temperature,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate structured educational presentation content and return strict JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        },
        timeout=90,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        if response.status_code == 404:
            raise RuntimeError(
                f"Gemini model '{model}' was not found. Update GEMINI_MODEL to 'gemini-2.5-flash'."
            ) from exc
        raise
    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini returned an empty response.")
    return "".join(part.get("text", "") for part in parts)


def _call_huggingface(prompt: str) -> str:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY is not configured.")

    model = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "inputs": prompt,
            "parameters": {
                "temperature": 0.3,
                "max_new_tokens": 1400,
                "return_full_text": False,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return first.get("generated_text", "")
    if isinstance(payload, dict) and payload.get("generated_text"):
        return payload["generated_text"]
    raise RuntimeError("Hugging Face returned an unexpected response format.")


def generate_slide_deck(input_text: str, density: str, level: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    cleaned = clean_text(input_text)
    topic_name = extract_topic_name(cleaned)
    prepared = prepare_text_for_llm(cleaned)
    density_instruction = "concise (3 bullets per slide)" if density == "concise" else "detailed (5-7 bullets per slide)"
    warnings: List[str] = []
    used_llm = False

    slides: List[Dict[str, Any]] = []
    quiz: List[Dict[str, Any]] = []

    if is_llm_configured():
        try:
            response_text = call_llm(build_slide_prompt(prepared["text"], level, density_instruction))
            slides_payload = _parse_llm_json_payload(response_text, "slides")
            slides = coerce_slides_structure(slides_payload, density)
            if not slides:
                raise InvalidLLMResponseError("Invalid LLM response")
            used_llm = True
        except InvalidLLMResponseError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Slide generation failed: {exc}") from exc
    else:
        slides = _generate_fallback_slides(cleaned, density)

    slides = ensure_teaching_flow(slides, cleaned, density, level, topic_name)

    if is_llm_configured():
        try:
            quiz_response = call_llm(build_quiz_prompt(slides, level), temperature=0.4)
            quiz_payload = _parse_llm_json_payload(quiz_response, "quiz")
            quiz = coerce_quiz_structure(quiz_payload, slides)
            used_llm = True
        except InvalidLLMResponseError as exc:
            warnings.append(str(exc))
        except Exception as exc:
            warnings.append(f"Quiz generation fallback: {exc}")

    if not quiz:
        quiz = heuristic_quiz(slides, level)

    return slides, quiz, {
        "topic": topic_name,
        "provider": get_provider_name(),
        "used_llm": used_llm,
        "chunked": prepared["chunked"],
        "chunk_count": prepared["chunk_count"],
        "warnings": warnings,
    }


def _generate_fallback_slides(input_text: str, density: str) -> List[Dict[str, Any]]:
    highlights = extract_key_lines(input_text, max_items=18)
    if not highlights:
        highlights = ["Introduce the uploaded notes", "Explain the major ideas", "Close with key takeaways"]

    group_size = 3 if density == "concise" else 5
    slides = []
    for index in range(0, len(highlights), group_size):
        group = highlights[index : index + group_size]
        if not group:
            continue
        title = _derive_slide_title(group[0], len(slides) + 1)
        slides.append({"title": title, "points": group})
        if len(slides) >= 5:
            break
    return slides


def _derive_slide_title(first_point: str, slide_number: int) -> str:
    words = first_point.replace(":", " ").split()
    if not words:
        return f"Concept {slide_number}"
    title = " ".join(words[:5]).strip(" ,.-")
    return title.title() if title else f"Concept {slide_number}"


def _parse_llm_json_payload(raw_text: str, label: str):
    logger.info("Raw %s LLM response: %s", label, raw_text)
    try:
        return parse_json_response(raw_text)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Invalid %s JSON from LLM: %s", label, exc)
        raise InvalidLLMResponseError("Invalid LLM response") from exc
