import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple

import requests

from utils import (
    build_data_slide,
    build_explanation_slide,
    build_slide,
    clean_text,
    coerce_quiz_structure,
    coerce_slides_structure,
    ensure_teaching_flow,
    extract_key_lines,
    extract_topic_name,
    heuristic_quiz,
    normalize_slide_type,
    parse_json_response,
    prepare_text_for_llm,
    preprocess_input_text,
)

logger = logging.getLogger(__name__)


class InvalidLLMResponseError(RuntimeError):
    pass


def build_slide_prompt(input_text: str, difficulty: str, density: str) -> str:
    return f"""Convert notes into structured slides.

Rules:
- Maintain teaching flow
- Detect difficult concepts and add explanation slides
- For each difficult concept, add an extra slide titled "<Concept> Explained Simply"
- Mark explanation slides with "extra_explanation": true
- Adjust difficulty: {difficulty}
- Adjust density: {density}
- Detect numeric data -> create data insight slide
- Use concise bullet points, never paragraphs

Return JSON:
[
  {{
    "title": "...",
    "points": ["..."],
    "type": "normal | explanation | data",
    "extra_explanation": false
  }}
]

Notes:
{input_text}
"""


def build_slide_regeneration_prompt(
    input_text: str,
    current_slide: Dict[str, Any],
    slide_index: int,
    slides: List[Dict[str, Any]],
    difficulty: str,
    density: str,
) -> str:
    titles = [slide.get("title", "") for slide in slides]
    serialized_context = json.dumps(titles, ensure_ascii=False)
    serialized_slide = json.dumps(current_slide, ensure_ascii=False, indent=2)

    return f"""Regenerate only one slide for an existing presentation.

Rules:
- Keep the presentation flow consistent with the surrounding slides
- Regenerate only slide index {slide_index}
- Preserve the requested slide purpose: {current_slide.get("type", "normal")}
- If the slide is an explanation slide, keep it simple and learner-friendly
- If the slide is a data slide, focus on numeric insights only
- Adjust difficulty: {difficulty}
- Adjust density: {density}
- Return ONLY valid JSON as one object:
{{
  "title": "...",
  "points": ["..."],
  "type": "normal | explanation | data",
  "extra_explanation": false
}}

Presentation slide titles:
{serialized_context}

Current slide to replace:
{serialized_slide}

Notes:
{input_text}
"""


def build_quiz_prompt(slides: List[Dict[str, Any]], difficulty: str) -> str:
    serialized_slides = json.dumps(slides, ensure_ascii=False, indent=2)
    return f"""Create 3 multiple-choice questions from the following slide content.

Rules:
- Each question must have exactly 4 options
- Keep the language suitable for difficulty: {difficulty}
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
                "max_new_tokens": 1600,
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
    cleaned_source = preprocess_input_text(input_text)
    topic_name = extract_topic_name(cleaned_source or input_text)
    prepared = prepare_text_for_llm(cleaned_source or input_text)
    density_instruction = "Concise (3 bullets per slide)" if density == "concise" else "Detailed (5-7 bullets per slide)"
    warnings: List[str] = []
    used_llm = False

    slides: List[Dict[str, Any]] = []
    quiz: List[Dict[str, Any]] = []

    if is_llm_configured():
        try:
            response_text = call_llm(build_slide_prompt(prepared["text"], level, density_instruction))
            slides_payload = _parse_llm_json_payload(response_text, "slides")
            slides = coerce_slides_structure(slides_payload, density, cleaned_source)
            if not slides:
                raise InvalidLLMResponseError("Invalid LLM response")
            used_llm = True
        except InvalidLLMResponseError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Slide generation failed: {exc}") from exc
    else:
        slides = _generate_fallback_slides(cleaned_source or input_text, density)

    slides = ensure_teaching_flow(slides, cleaned_source or input_text, density, level, topic_name)

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
        "preprocessed": cleaned_source,
    }


def regenerate_specific_slide(
    input_text: str,
    slide_index: int,
    slides: List[Dict[str, Any]],
    density: str,
    level: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if slide_index < 0 or slide_index >= len(slides):
        raise ValueError("Slide index is out of range.")

    cleaned_source = preprocess_input_text(input_text)
    density_instruction = "Concise (3 bullets per slide)" if density == "concise" else "Detailed (5-7 bullets per slide)"
    current_slide = slides[slide_index]
    warnings: List[str] = []
    used_llm = False

    regenerated_slide = None

    if is_llm_configured():
        try:
            response_text = call_llm(
                build_slide_regeneration_prompt(
                    cleaned_source or input_text,
                    current_slide,
                    slide_index,
                    slides,
                    level,
                    density_instruction,
                )
            )
            payload = _parse_llm_json_payload(response_text, f"slide {slide_index}")
            if isinstance(payload, list):
                payload = payload[0] if payload else {}
            regenerated_slide = _coerce_single_slide(payload, density, cleaned_source or input_text, current_slide)
            used_llm = True
        except InvalidLLMResponseError:
            raise
        except Exception as exc:
            warnings.append(f"Regeneration fallback: {exc}")

    if regenerated_slide is None:
        regenerated_slide = _fallback_regenerated_slide(current_slide, cleaned_source or input_text, density)

    return regenerated_slide, {
        "provider": get_provider_name(),
        "used_llm": used_llm,
        "warnings": warnings,
    }


def _generate_fallback_slides(input_text: str, density: str) -> List[Dict[str, Any]]:
    highlights = extract_key_lines(input_text, max_items=20)
    if not highlights:
        highlights = ["Introduce the uploaded notes", "Explain the major ideas", "Close with key takeaways"]

    group_size = 3 if density == "concise" else 5
    slides = []
    for index in range(0, len(highlights), group_size):
        group = highlights[index : index + group_size]
        if not group:
            continue
        title = _derive_slide_title(group[0], len(slides) + 1)
        slides.append(build_slide(title, group, density, slide_type="normal"))
        if len(slides) >= 5:
            break
    return slides


def _derive_slide_title(first_point: str, slide_number: int) -> str:
    words = first_point.replace(":", " ").split()
    if not words:
        return f"Concept {slide_number}"
    title = " ".join(words[:5]).strip(" ,.-")
    return title.title() if title else f"Concept {slide_number}"


def _coerce_single_slide(
    payload: Any,
    density: str,
    source_text: str,
    current_slide: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise InvalidLLMResponseError("Invalid LLM response")

    coerced = coerce_slides_structure([payload], density, source_text)
    if not coerced:
        raise InvalidLLMResponseError("Invalid LLM response")

    slide = coerced[0]
    current_type = normalize_slide_type(current_slide.get("type"), current_slide.get("title", ""))
    if current_type == "explanation" and slide["type"] == "normal":
        slide["type"] = "explanation"
        slide["extra_explanation"] = True
    if current_type == "data" and slide["type"] != "data":
        data_slide = build_data_slide(source_text, density)
        if data_slide:
            return data_slide
    return slide


def _fallback_regenerated_slide(current_slide: Dict[str, Any], input_text: str, density: str) -> Dict[str, Any]:
    current_type = normalize_slide_type(current_slide.get("type"), current_slide.get("title", ""))

    if current_type == "data":
        data_slide = build_data_slide(input_text, density)
        if data_slide:
            return data_slide

    if current_type == "explanation":
        return build_explanation_slide(current_slide, density)

    title = current_slide.get("title", "Regenerated Slide")
    highlights = _select_relevant_highlights(input_text, title, max_items=7 if density == "detailed" else 3)
    if not highlights:
        highlights = current_slide.get("points") or [f"Revisit the key idea behind {title.lower()}"]

    return build_slide(
        title,
        highlights,
        density,
        slide_type=current_type,
        extra_explanation=bool(current_slide.get("extra_explanation")),
        chart_data=current_slide.get("chart_data") or [],
    )


def _select_relevant_highlights(text: str, title: str, max_items: int) -> List[str]:
    title_tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]*", clean_text(title))
        if len(token) > 3
    }
    highlights = []

    for sentence in extract_key_lines(text, max_items=16):
        lowered = sentence.lower()
        if title_tokens and any(token in lowered for token in title_tokens):
            highlights.append(sentence)
        if len(highlights) >= max_items:
            break

    if highlights:
        return highlights[:max_items]
    return extract_key_lines(text, max_items=max_items)


def _parse_llm_json_payload(raw_text: str, label: str):
    logger.info("Raw %s LLM response: %s", label, raw_text)
    try:
        return parse_json_response(raw_text)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Invalid %s JSON from LLM: %s", label, exc)
        raise InvalidLLMResponseError("Invalid LLM response") from exc
