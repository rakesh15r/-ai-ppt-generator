import io
import json
import os
import re
from typing import Any, Dict, List, Optional

import pdfplumber
from pypdf import PdfReader


DENSITY_LIMITS = {
    "concise": (3, 3),
    "detailed": (5, 7),
}

VALID_SLIDE_TYPES = {"normal", "explanation", "data"}

COMPLEX_CONCEPT_HINTS = {
    "algorithm",
    "architecture",
    "backpropagation",
    "bayesian",
    "calculus",
    "classification",
    "compiler",
    "convolution",
    "correlation",
    "cryptography",
    "derivative",
    "distributed",
    "embedding",
    "entropy",
    "framework",
    "gradient",
    "heuristic",
    "inference",
    "integration",
    "matrix",
    "neural",
    "normalization",
    "optimization",
    "probability",
    "protocol",
    "regression",
    "synchronization",
    "transformer",
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


def preprocess_input_text(text: str) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    raw_lines = [clean_text(line) for line in cleaned.splitlines()]
    filtered_lines: List[str] = []
    seen_lines = set()

    for line in raw_lines:
        if not line:
            continue
        words = re.findall(r"[A-Za-z0-9%]+", line)
        if len(words) < 3 and not _looks_meaningful_short_line(line):
            continue
        key = _normalize_dedupe_key(line)
        if not key or key in seen_lines:
            continue
        seen_lines.add(key)
        filtered_lines.append(line)

    if not filtered_lines:
        filtered_lines = [cleaned]

    deduped_sentences: List[str] = []
    seen_sentences = set()

    for line in filtered_lines:
        parts = re.split(r"(?<=[.!?])\s+", line)
        kept_parts = []
        for part in parts:
            normalized = normalize_point(part)
            if not normalized:
                continue
            key = _normalize_dedupe_key(normalized)
            if key in seen_sentences:
                continue
            seen_sentences.add(key)
            kept_parts.append(normalized)
        if kept_parts:
            deduped_sentences.append(" ".join(kept_parts))

    return clean_text("\n".join(deduped_sentences))


def _looks_meaningful_short_line(line: str) -> bool:
    words = re.findall(r"[A-Za-z0-9%]+", line)
    if re.search(r"\d", line):
        return True
    if re.search(r"[A-Z]{2,}", line):
        return True
    if len(words) >= 2 and all(word[:1].isupper() for word in words if word[:1].isalpha()):
        return True
    if any(len(word) >= 8 for word in words):
        return True
    if line.endswith(":"):
        return True
    return False


def _normalize_dedupe_key(text: str) -> str:
    return re.sub(r"[^a-z0-9%]+", " ", clean_text(text).lower()).strip()


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
    cleaned = preprocess_input_text(text)
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


def normalize_slide_type(value: Any, title: str = "") -> str:
    slide_type = clean_text(str(value or "")).lower()
    if slide_type in VALID_SLIDE_TYPES:
        return slide_type

    lowered_title = clean_text(title).lower()
    if "explained simply" in lowered_title:
        return "explanation"
    if "data insight" in lowered_title or "data insights" in lowered_title:
        return "data"
    return "normal"


def build_slide(
    title: str,
    points: List[str],
    density: str,
    slide_type: str = "normal",
    extra_explanation: bool = False,
    chart_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    normalized_type = normalize_slide_type(slide_type, title)
    normalized_chart = coerce_chart_data(chart_data or [])
    return {
        "title": clean_text(title)[:120] or "Untitled Slide",
        "points": coerce_points(points, density, title),
        "type": normalized_type,
        "extra_explanation": bool(extra_explanation or normalized_type == "explanation"),
        "chart_data": normalized_chart if normalized_type == "data" else [],
    }


def coerce_chart_data(chart_data: Any) -> List[Dict[str, Any]]:
    if not isinstance(chart_data, list):
        return []

    normalized = []
    seen = set()
    for item in chart_data:
        if not isinstance(item, dict):
            continue
        label = clean_text(str(item.get("label") or ""))
        value = item.get("value")
        unit = clean_text(str(item.get("unit") or ""))
        if not label:
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        key = (label.lower(), numeric_value, unit)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "label": label[:48],
                "value": numeric_value,
                "unit": unit,
            }
        )
    return normalized[:6]


def coerce_slides_structure(slides: Any, density: str, source_text: str = "") -> List[Dict[str, Any]]:
    if not isinstance(slides, list):
        return []

    validated: List[Dict[str, Any]] = []
    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            continue

        title = clean_text(str(slide.get("title") or f"Slide {index}"))[:120]
        slide_type = normalize_slide_type(slide.get("type"), title)
        chart_data = coerce_chart_data(slide.get("chart_data") or [])
        points = coerce_points(slide.get("points", []), density, title)

        if slide_type == "data" and not chart_data:
            chart_data = extract_chart_data("\n".join(points) or source_text)

        validated.append(
            {
                "title": title or f"Slide {index}",
                "points": points,
                "type": slide_type,
                "extra_explanation": bool(slide.get("extra_explanation") or slide_type == "explanation"),
                "chart_data": chart_data if slide_type == "data" else [],
            }
        )

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
            merged.append(
                {
                    "title": slide["title"],
                    "points": list(slide["points"]),
                    "type": normalize_slide_type(slide.get("type"), slide["title"]),
                    "extra_explanation": bool(slide.get("extra_explanation")),
                    "chart_data": coerce_chart_data(slide.get("chart_data") or []),
                }
            )
            continue

        existing = merged[title_index[key]]
        combined_points = existing["points"] + slide["points"]
        existing["points"] = coerce_points(combined_points, density, existing["title"])
        existing["extra_explanation"] = bool(existing["extra_explanation"] or slide.get("extra_explanation"))
        existing["type"] = _prefer_slide_type(existing.get("type"), slide.get("type"), existing["title"])
        existing["chart_data"] = _merge_chart_data(existing.get("chart_data"), slide.get("chart_data"))

    return merged


def _prefer_slide_type(current: Any, incoming: Any, title: str) -> str:
    current_type = normalize_slide_type(current, title)
    incoming_type = normalize_slide_type(incoming, title)
    if current_type == incoming_type:
        return current_type
    if "data" in {current_type, incoming_type}:
        return "data"
    if "explanation" in {current_type, incoming_type}:
        return "explanation"
    return "normal"


def _merge_chart_data(first: Any, second: Any) -> List[Dict[str, Any]]:
    return coerce_chart_data((first or []) + (second or []))


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
    return build_slide("Introduction", points, density)


def build_process_slide(steps: List[str], density: str) -> Dict[str, Any]:
    formatted = [f"Step {index}: {step}" for index, step in enumerate(steps, start=1)]
    return build_slide("Process Flow", formatted, density)


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
    return build_slide("Worked Example", points, density)


def build_summary_slide(slides: List[Dict[str, Any]], density: str) -> Dict[str, Any]:
    highlights: List[str] = []
    for slide in slides:
        title = slide["title"].strip()
        lowered = title.lower()
        if lowered in {"introduction", "worked example", "summary", "process flow", "data insights"}:
            continue
        if slide.get("type") == "explanation":
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

    return build_slide("Summary", highlights, density)


def build_explanation_slide(source_slide: Dict[str, Any], density: str) -> Dict[str, Any]:
    concept = source_slide["title"]
    concept_points = source_slide.get("points") or []
    first_point = concept_points[0] if concept_points else concept.lower()
    second_point = concept_points[1] if len(concept_points) > 1 else f"{concept} supports the lesson objective"

    points = [
        f"Think of {concept} as the core idea behind {simplify_sentence(first_point, concept)}",
        f"In simpler terms, {simplify_sentence(second_point, concept)}",
        f"Focus on what {concept.lower()} does before worrying about the technical labels",
        f"Teach it step by step using one clear classroom example",
        f"Remember the main takeaway: {concept} connects concept, action, and outcome",
    ]
    return build_slide(
        f"{concept} Explained Simply",
        points,
        density,
        slide_type="explanation",
        extra_explanation=True,
    )


def simplify_sentence(text: str, concept: str) -> str:
    simplified = normalize_point(text)
    simplified = re.sub(r"\b(optimiz(?:e|ation)|algorithm|architecture|parameter|synchronization)\b", "main idea", simplified, flags=re.IGNORECASE)
    simplified = simplified[:120].rstrip(" ,.;:")
    if not simplified:
        simplified = f"{concept.lower()} works as a simple step in the lesson"
    if simplified[0].isupper():
        simplified = simplified[0].lower() + simplified[1:]
    return simplified


def extract_chart_data(text: str, limit: int = 6) -> List[Dict[str, Any]]:
    cleaned = preprocess_input_text(text)
    if not re.search(r"\d", cleaned):
        return []

    chart_data: List[Dict[str, Any]] = []
    seen = set()

    for line in cleaned.splitlines():
        segments = [segment.strip() for segment in re.split(r"[;|]", line) if segment.strip()]
        if not segments:
            segments = [line]
        for segment in segments:
            for item in _extract_numeric_pairs_from_segment(segment):
                key = (item["label"].lower(), item["value"], item["unit"])
                if key in seen:
                    continue
                seen.add(key)
                chart_data.append(item)
                if len(chart_data) >= limit:
                    return chart_data[:limit]

    return chart_data[:limit]


def _extract_numeric_pairs_from_segment(segment: str) -> List[Dict[str, Any]]:
    pairs: List[Dict[str, Any]] = []
    segment = clean_text(segment)
    if not segment or not re.search(r"\d", segment):
        return pairs

    colon_match = re.match(r"(.{2,60}?):\s*(-?\d+(?:\.\d+)?)\s*(%|percent)?", segment, re.IGNORECASE)
    if colon_match:
        label = _sanitize_chart_label(colon_match.group(1))
        value = float(colon_match.group(2))
        unit = "%" if colon_match.group(3) else ""
        if label:
            pairs.append({"label": label, "value": value, "unit": unit})
        return pairs

    matches = re.finditer(
        r"([A-Za-z][A-Za-z0-9 /()'-]{2,40}?)\s*(?:=|is|was|were|at|to|reached|hit|stood at)?\s*(-?\d+(?:\.\d+)?)\s*(%|percent)?",
        segment,
        re.IGNORECASE,
    )
    for match in matches:
        label = _sanitize_chart_label(match.group(1))
        if not label:
            continue
        value = float(match.group(2))
        unit = "%" if match.group(3) else ""
        pairs.append({"label": label, "value": value, "unit": unit})

    if pairs:
        return pairs

    first_number = re.search(r"(-?\d+(?:\.\d+)?)\s*(%|percent)?", segment, re.IGNORECASE)
    if first_number:
        label = _sanitize_chart_label(re.sub(r"(-?\d+(?:\.\d+)?)\s*(%|percent)?", "", segment, count=1, flags=re.IGNORECASE))
        if label:
            pairs.append(
                {
                    "label": label,
                    "value": float(first_number.group(1)),
                    "unit": "%" if first_number.group(2) else "",
                }
            )
    return pairs


def _sanitize_chart_label(label: str) -> str:
    sanitized = clean_text(label)
    sanitized = re.sub(r"\b(is|was|were|at|to|reached|hit|stood)\b$", "", sanitized, flags=re.IGNORECASE).strip(" :-")
    sanitized = sanitized[:40]
    if not sanitized or len(re.findall(r"[A-Za-z]", sanitized)) < 2:
        return ""
    return sanitized


def build_data_slide(source_text: str, density: str) -> Optional[Dict[str, Any]]:
    chart_data = extract_chart_data(source_text)
    if not chart_data:
        return None

    points = []
    for item in chart_data:
        value_text = f"{item['value']:.2f}".rstrip("0").rstrip(".")
        if item.get("unit") == "%":
            value_text = f"{value_text}%"
        points.append(f"{item['label']} is reported at {value_text}")

    if len(chart_data) >= 2:
        highest = max(chart_data, key=lambda item: item["value"])
        lowest = min(chart_data, key=lambda item: item["value"])
        points.append(f"{highest['label']} is the strongest data point in the material")
        if highest["label"] != lowest["label"]:
            points.append(f"{lowest['label']} is the lowest comparison point to discuss")

    return build_slide(
        "Data Insights",
        points,
        density,
        slide_type="data",
        chart_data=chart_data,
    )


def is_complex_slide(slide: Dict[str, Any], difficulty: str) -> bool:
    if slide.get("type") != "normal":
        return False

    lowered = f"{slide.get('title', '')} {' '.join(slide.get('points') or [])}".lower()
    if slide.get("title", "").lower() in {"introduction", "summary", "worked example", "process flow", "data insights"}:
        return False

    keyword_hits = sum(1 for term in COMPLEX_CONCEPT_HINTS if term in lowered)
    long_words = [word for word in re.findall(r"[a-zA-Z]{9,}", lowered) if word not in STOPWORDS]
    complexity_score = keyword_hits + min(len(long_words), 4)

    level = clean_text(difficulty).lower()
    if level == "beginner":
        return complexity_score >= 2
    if level == "intermediate":
        return complexity_score >= 3
    return complexity_score >= 4


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

    ordered = _insert_explanation_slides(ordered, density, difficulty)

    example_idx = _find_slide_index(ordered, ("example", "scenario", "application", "case"))
    if example_idx is None:
        ordered.append(build_example_slide(topic_name, source_text, density))

    ordered = _ensure_data_slide(ordered, source_text, density)
    ordered = _ensure_summary_slide(ordered, density)

    return [
        {
            "title": slide["title"],
            "points": coerce_points(slide["points"], density, slide["title"]),
            "type": normalize_slide_type(slide.get("type"), slide["title"]),
            "extra_explanation": bool(slide.get("extra_explanation")),
            "chart_data": coerce_chart_data(slide.get("chart_data") or []),
        }
        for slide in ordered
    ]


def _insert_explanation_slides(slides: List[Dict[str, Any]], density: str, difficulty: str) -> List[Dict[str, Any]]:
    existing_titles = {re.sub(r"[^a-z0-9]+", "", slide["title"].lower()) for slide in slides}
    enriched: List[Dict[str, Any]] = []

    for index, slide in enumerate(slides):
        enriched.append(slide)
        if not is_complex_slide(slide, difficulty):
            continue

        explanation_title = f"{slide['title']} Explained Simply"
        explanation_key = re.sub(r"[^a-z0-9]+", "", explanation_title.lower())
        if explanation_key in existing_titles:
            continue

        next_slide = slides[index + 1] if index + 1 < len(slides) else None
        if next_slide and normalize_slide_type(next_slide.get("type"), next_slide.get("title", "")) == "explanation":
            continue

        explanation_slide = build_explanation_slide(slide, density)
        enriched.append(explanation_slide)
        existing_titles.add(explanation_key)

    return enriched


def _ensure_data_slide(slides: List[Dict[str, Any]], source_text: str, density: str) -> List[Dict[str, Any]]:
    existing_data_index = _find_slide_index(slides, ("data insight", "data insights"))
    summary_index = _find_slide_index(slides, ("summary", "conclusion", "takeaway", "recap"))

    if existing_data_index is not None:
        if not slides[existing_data_index].get("chart_data"):
            slides[existing_data_index]["chart_data"] = extract_chart_data(source_text)
        return slides

    data_slide = build_data_slide(source_text, density)
    if not data_slide:
        return slides

    insert_at = summary_index if summary_index is not None else len(slides)
    slides.insert(insert_at, data_slide)
    return slides


def _ensure_summary_slide(slides: List[Dict[str, Any]], density: str) -> List[Dict[str, Any]]:
    existing_summary = _find_slide_index(slides, ("summary", "conclusion", "takeaway", "recap"))
    if existing_summary is not None:
        base_slides = [slide for index, slide in enumerate(slides) if index != existing_summary]
    else:
        base_slides = slides

    summary_slide = build_summary_slide(base_slides, density)
    filtered = [slide for slide in base_slides if "summary" not in slide["title"].lower()]
    filtered.append(summary_slide)
    return filtered


def _find_slide_index(slides: List[Dict[str, Any]], keywords: tuple) -> Optional[int]:
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
