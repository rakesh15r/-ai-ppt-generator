import io
import json
import os
import re
from typing import Any, Dict, List

import pdfplumber
from pypdf import PdfReader


DENSITY_LIMITS = {
    "concise": (3, 3),
    "detailed": (5, 7),
}


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "using",
    "with",
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\r", "\n").replace("\x00", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"[^\S\n]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_text_from_file(file_storage) -> str:
    filename = (file_storage.filename or "").strip()
    extension = os.path.splitext(filename.lower())[1]
    payload = file_storage.read()
    file_storage.stream.seek(0)

    if extension == ".pdf":
        text = _extract_pdf_text(payload)
    elif extension == ".txt":
        text = payload.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Upload a PDF or TXT file.")

    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("The uploaded file did not contain readable text.")
    return cleaned


def _extract_pdf_text(payload: bytes) -> str:
    text_chunks: List[str] = []

    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        for page in pdf.pages:
            text_chunks.append(page.extract_text() or "")

    merged = clean_text("\n".join(text_chunks))
    if merged:
        return merged

    reader = PdfReader(io.BytesIO(payload))
    fallback_pages = []
    for page in reader.pages:
        fallback_pages.append(page.extract_text() or "")
    return "\n".join(fallback_pages)


def chunk_text(text: str, max_chars: int = 3200, overlap: int = 250) -> List[str]:
    text = clean_text(text)
    if len(text) <= max_chars:
        return [text] if text else []

    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = min(start + max_chars, len(paragraph))
            piece = paragraph[start:end].strip()
            if piece:
                chunks.append(piece)
            if end >= len(paragraph):
                break
            start = max(0, end - overlap)
        current = ""

    if current:
        chunks.append(current)

    return chunks


def sentence_fragments(text: str) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    fragments = []
    for part in raw_parts:
        normalized = normalize_point(part)
        if len(normalized) >= 8:
            fragments.append(normalized)
    return fragments


def extract_key_lines(text: str, max_items: int = 8) -> List[str]:
    candidates = sentence_fragments(text)
    if not candidates:
        return []

    selected: List[str] = []
    seen = set()
    for candidate in candidates:
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(candidate)
        if len(selected) >= max_items:
            break
    return selected


def prepare_text_for_llm(text: str, max_chars: int = 7000) -> Dict[str, Any]:
    cleaned = clean_text(text)
    chunks = chunk_text(cleaned)

    if len(chunks) <= 1 and len(cleaned) <= max_chars:
        return {
            "text": cleaned,
            "chunked": False,
            "chunk_count": len(chunks) or 1,
        }

    summaries = []
    for index, chunk in enumerate(chunks, start=1):
        highlights = extract_key_lines(chunk, max_items=7)
        summary_lines = "\n".join(f"- {item}" for item in highlights) or "- No extractable highlights"
        summaries.append(f"Section {index} Highlights:\n{summary_lines}")

    prepared = "\n\n".join(summaries)
    if len(prepared) > max_chars:
        prepared = prepared[:max_chars].rsplit(" ", 1)[0]

    return {
        "text": prepared,
        "chunked": True,
        "chunk_count": len(chunks),
    }


def normalize_point(value: Any) -> str:
    text = clean_text(str(value or ""))
    text = re.sub(r"^[-*•\d.)\s]+", "", text)
    return text.strip(" -•\t")


def density_bounds(density: str) -> tuple:
    return DENSITY_LIMITS.get((density or "").lower(), (3, 5))


def coerce_points(points: Any, density: str, slide_title: str) -> List[str]:
    min_points, max_points = density_bounds(density)

    if isinstance(points, str):
        raw_points = re.split(r"\n+|;(?=\s+[A-Z])", points)
    elif isinstance(points, list):
        raw_points = points
    else:
        raw_points = []

    normalized: List[str] = []
    seen = set()

    for item in raw_points:
        item = normalize_point(item)
        if not item:
            continue
        if len(item) > 140 and ";" in item:
            parts = [normalize_point(part) for part in item.split(";")]
        else:
            parts = [item]

        for part in parts:
            key = part.lower()
            if len(part) < 4 or key in seen:
                continue
            seen.add(key)
            normalized.append(part)
            if len(normalized) >= max_points:
                break
        if len(normalized) >= max_points:
            break

    while len(normalized) < min_points:
        normalized.append(_fallback_point(slide_title, len(normalized)))

    return normalized[:max_points]


def _fallback_point(slide_title: str, index: int) -> str:
    base = slide_title.lower() if slide_title else "the topic"
    templates = [
        f"Define the main idea behind {base}",
        f"Connect {base} to the lesson objective",
        f"Highlight the most important learner takeaway",
        f"Show where {base} fits in the overall teaching flow",
        f"Reinforce the concept with a practical classroom angle",
        f"Clarify the key detail students should retain",
        f"Link the idea to a likely application or example",
    ]
    return templates[index % len(templates)]


def coerce_slides_structure(slides: Any, density: str) -> List[Dict[str, Any]]:
    if not isinstance(slides, list):
        return []

    validated: List[Dict[str, Any]] = []
    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            continue
        title = clean_text(str(slide.get("title") or f"Slide {index}"))[:120]
        points = coerce_points(slide.get("points", []), density, title)
        validated.append({"title": title or f"Slide {index}", "points": points})
    return dedupe_slides(validated, density)


def dedupe_slides(slides: List[Dict[str, Any]], density: str) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    title_index: Dict[str, int] = {}

    for slide in slides:
        key = re.sub(r"[^a-z0-9]+", "", slide["title"].lower())
        if not key:
            key = f"slide{len(merged) + 1}"
        if key not in title_index:
            title_index[key] = len(merged)
            merged.append({"title": slide["title"], "points": list(slide["points"])})
            continue

        existing = merged[title_index[key]]
        combined = existing["points"] + slide["points"]
        existing["points"] = coerce_points(combined, density, existing["title"])

    return merged


def extract_topic_name(text: str) -> str:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", clean_text(text))
    topic_tokens = [token for token in tokens if token.lower() not in STOPWORDS][:6]
    if not topic_tokens:
        return "Class Slides"
    return " ".join(topic_tokens).title()


def detect_process_steps(text: str, limit: int = 6) -> List[str]:
    steps: List[str] = []
    for line in clean_text(text).splitlines():
        match = re.match(r"^\s*(?:step\s*\d+[:.)-]?|\d+[.)-]|[-*])\s+(.+)$", line, re.IGNORECASE)
        if match:
            steps.append(normalize_point(match.group(1)))
        if len(steps) >= limit:
            return steps[:limit]

    if len(steps) >= 3:
        return steps[:limit]

    candidates = sentence_fragments(text)
    transition_words = ("first", "next", "then", "after", "finally", "before")
    for sentence in candidates:
        lowered = sentence.lower()
        if any(word in lowered for word in transition_words):
            steps.append(sentence)
        if len(steps) >= limit:
            break

    return steps[:limit] if len(steps) >= 3 else []


def extract_example_points(text: str, limit: int = 5) -> List[str]:
    keywords = ("example", "for instance", "for example", "e.g.", "case", "scenario")
    examples = []
    for sentence in sentence_fragments(text):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            examples.append(sentence)
        if len(examples) >= limit:
            break
    return examples


def build_intro_slide(topic_name: str, density: str, difficulty: str) -> Dict[str, Any]:
    points = [
        f"Introduce the scope of {topic_name}",
        "Explain why the topic matters in teaching or learning",
        f"Set expectations for a {difficulty.lower()} audience",
        "Outline the concepts that will be covered next",
        "Connect the lesson to a practical classroom outcome",
    ]
    return {
        "title": "Introduction",
        "points": coerce_points(points, density, "Introduction"),
    }


def build_process_slide(steps: List[str], density: str) -> Dict[str, Any]:
    formatted = [f"Step {index}: {step}" for index, step in enumerate(steps, start=1)]
    return {
        "title": "Process Flow",
        "points": coerce_points(formatted, density, "Process Flow"),
    }


def build_example_slide(topic_name: str, text: str, density: str) -> Dict[str, Any]:
    points = extract_example_points(text, limit=density_bounds(density)[1])
    if not points:
        points = [
            f"Use a realistic classroom scenario involving {topic_name}",
            "Walk through the decision, action, and outcome",
            "Show how the concept appears in practice",
            "Point out what learners should notice in the example",
            "Relate the example back to the core concepts",
        ]
    return {
        "title": "Worked Example",
        "points": coerce_points(points, density, "Worked Example"),
    }


def build_summary_slide(slides: List[Dict[str, Any]], density: str) -> Dict[str, Any]:
    highlights: List[str] = []
    for slide in slides:
        title = slide["title"].strip()
        lowered = title.lower()
        if lowered in {"introduction", "worked example", "summary", "process flow"}:
            continue
        highlights.append(f"Revisit {title.lower()} as a key takeaway")
        if len(highlights) >= density_bounds(density)[1]:
            break

    if not highlights:
        highlights = [
            "Review the central concepts from the lesson",
            "Reinforce the most important relationships and terms",
            "Close with the practical takeaway for learners",
        ]

    return {
        "title": "Summary",
        "points": coerce_points(highlights, density, "Summary"),
    }


def ensure_teaching_flow(
    slides: List[Dict[str, Any]],
    source_text: str,
    density: str,
    difficulty: str,
    topic_name: str,
) -> List[Dict[str, Any]]:
    ordered = dedupe_slides(slides, density)

    intro_idx = _find_slide_index(ordered, ("introduction", "overview", "foundations"))
    if intro_idx is None:
        ordered.insert(0, build_intro_slide(topic_name, density, difficulty))
    elif intro_idx != 0:
        ordered.insert(0, ordered.pop(intro_idx))

    process_steps = detect_process_steps(source_text)
    process_idx = _find_slide_index(ordered, ("process", "workflow", "steps", "procedure"))
    if process_steps and process_idx is None:
        insert_at = min(2, len(ordered))
        ordered.insert(insert_at, build_process_slide(process_steps, density))

    example_idx = _find_slide_index(ordered, ("example", "scenario", "application", "case"))
    if example_idx is None:
        summary_idx = _find_slide_index(ordered, ("summary", "conclusion", "takeaway", "recap"))
        insert_at = summary_idx if summary_idx is not None else len(ordered)
        ordered.insert(insert_at, build_example_slide(topic_name, source_text, density))

    summary_idx = _find_slide_index(ordered, ("summary", "conclusion", "takeaway", "recap"))
    if summary_idx is None:
        ordered.append(build_summary_slide(ordered, density))
    elif summary_idx != len(ordered) - 1:
        ordered.append(ordered.pop(summary_idx))

    return [
        {
            "title": slide["title"],
            "points": coerce_points(slide["points"], density, slide["title"]),
        }
        for slide in ordered
    ]


def _find_slide_index(slides: List[Dict[str, Any]], keywords: tuple) -> int:
    for index, slide in enumerate(slides):
        lowered = slide["title"].lower()
        if any(keyword in lowered for keyword in keywords):
            return index
    return None


def find_json_payload(text: str) -> str:
    if not text:
        raise ValueError("The LLM response was empty.")

    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    if cleaned.startswith("[") or cleaned.startswith("{"):
        return cleaned

    start_positions = [pos for pos in (cleaned.find("["), cleaned.find("{")) if pos != -1]
    if not start_positions:
        raise ValueError("No JSON payload found in the LLM response.")

    start = min(start_positions)
    opener = cleaned[start]
    closer = "]" if opener == "[" else "}"

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return cleaned[start : index + 1]

    raise ValueError("The LLM response did not contain complete JSON.")


def parse_json_response(text: str) -> Any:
    return json.loads(find_json_payload(text))


def coerce_quiz_structure(quiz: Any, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(quiz, list):
        return []

    fallback_options = []
    for slide in slides:
        fallback_options.extend(slide["points"])

    questions = []
    for item in quiz:
        if not isinstance(item, dict):
            continue
        question = clean_text(str(item.get("question") or ""))
        answer = clean_text(str(item.get("answer") or ""))
        options = item.get("options") or []
        if isinstance(options, str):
            options = [normalize_point(option) for option in options.split("\n")]
        options = [clean_text(str(option)) for option in options if clean_text(str(option))]

        if answer and answer not in options:
            options = [answer] + options

        seen = set()
        unique_options = []
        for option in options + fallback_options:
            option = clean_text(str(option))
            if not option or option.lower() in seen:
                continue
            seen.add(option.lower())
            unique_options.append(option)
            if len(unique_options) >= 4:
                break

        if not question or len(unique_options) < 4:
            continue

        resolved_answer = answer if answer in unique_options else unique_options[0]
        questions.append(
            {
                "question": question,
                "options": unique_options[:4],
                "answer": resolved_answer,
            }
        )
        if len(questions) >= 3:
            break

    return questions


def heuristic_quiz(slides: List[Dict[str, Any]], difficulty: str) -> List[Dict[str, Any]]:
    questions = []
    source_points = [point for slide in slides for point in slide["points"]]

    for slide in slides:
        title = slide["title"]
        if title.lower() in {"introduction", "summary"}:
            continue
        answer = slide["points"][0]
        options = [answer]
        for point in source_points:
            if point not in options:
                options.append(point)
            if len(options) >= 4:
                break
        if len(options) < 4:
            continue
        questions.append(
            {
                "question": f"For a {difficulty.lower()} learner, which point best fits the slide '{title}'?",
                "options": options[:4],
                "answer": answer,
            }
        )
        if len(questions) >= 3:
            break

    return questions


def slugify_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", clean_text(value).lower()).strip("-")
    return cleaned or "class-slides"
