import logging
import uuid

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from llm import InvalidLLMResponseError, generate_slide_deck, regenerate_specific_slide
from ppt_generator import build_presentation
from utils import (
    clean_text,
    coerce_quiz_structure,
    coerce_slides_structure,
    extract_text_from_file,
    preprocess_input_text,
    slugify_filename,
)


logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
CORS(app)

SESSION_STORE = {}


def json_response(payload, status=200):
    app.logger.info("Sending JSON response (%s): %s", status, payload)
    response = jsonify(payload)
    response.status_code = status
    response.headers["Content-Type"] = "application/json"
    return response


@app.post("/generate-slides")
def generate_slides():
    try:
        text_input = request.form.get("text", "")
        density = (request.form.get("density", "concise") or "concise").lower()
        difficulty = (request.form.get("difficulty", "Beginner") or "Beginner").title()
        uploaded_file = request.files.get("file")

        source_parts = []
        if clean_text(text_input):
            source_parts.append(clean_text(text_input))

        if uploaded_file and uploaded_file.filename:
            source_parts.append(extract_text_from_file(uploaded_file))

        if not source_parts:
            return json_response({"error": "Provide notes in the text box or upload a PDF/TXT file."}, 400)

        raw_source_text = "\n\n".join(source_parts)
        cleaned_source_text = preprocess_input_text(raw_source_text)
        slides, quiz, metadata = generate_slide_deck(cleaned_source_text or raw_source_text, density=density, level=difficulty)

        session_id = str(uuid.uuid4())
        SESSION_STORE[session_id] = {
            "slides": slides,
            "quiz": quiz,
            "topic": metadata.get("topic", "Class Slides"),
            "density": density,
            "difficulty": difficulty,
            "source_text": cleaned_source_text or raw_source_text,
            "original_source_text": raw_source_text,
        }

        return json_response(
            {
                "session_id": session_id,
                "slides": slides,
                "quiz": quiz,
                "download_url": f"/download-ppt?session_id={session_id}",
                "metadata": metadata,
            }
        )
    except InvalidLLMResponseError:
        app.logger.exception("LLM returned invalid JSON.")
        return json_response({"error": "Invalid LLM response"}, 500)
    except ValueError as error:
        app.logger.warning("Invalid request for /generate-slides: %s", error)
        return json_response({"error": str(error) or "Invalid input"}, 400)
    except Exception as error:
        app.logger.exception("Unexpected error in /generate-slides")
        return json_response({"error": str(error) or "Something went wrong"}, 500)


@app.post("/sync-session/<session_id>")
def sync_session(session_id):
    try:
        session = SESSION_STORE.get(session_id)
        if not session:
            return json_response({"error": "Session not found. Generate slides again."}, 404)

        payload = request.get_json(silent=True) or {}
        slides = payload.get("slides", session["slides"])
        quiz = payload.get("quiz", session["quiz"])

        session["slides"] = coerce_slides_structure(slides, session["density"], session["source_text"])
        session["quiz"] = coerce_quiz_structure(quiz, session["slides"])

        return json_response({"message": "Session updated.", "slides": session["slides"], "quiz": session["quiz"]})
    except Exception as error:
        app.logger.exception("Unexpected error in /sync-session/%s", session_id)
        return json_response({"error": str(error) or "Something went wrong"}, 500)


@app.post("/regenerate-slide")
def regenerate_slide():
    try:
        payload = request.get_json(silent=True) or {}
        session_id = clean_text(str(payload.get("session_id") or ""))
        slide_index = payload.get("slide_index")
        notes = payload.get("notes")

        if not session_id:
            return json_response({"error": "session_id is required."}, 400)

        session = SESSION_STORE.get(session_id)
        if not session:
            return json_response({"error": "Session not found. Generate slides again."}, 404)

        try:
            slide_index = int(slide_index)
        except (TypeError, ValueError):
            return json_response({"error": "slide_index must be a valid integer."}, 400)

        source_text = preprocess_input_text(notes) if notes else session["source_text"]
        regenerated_slide, metadata = regenerate_specific_slide(
            source_text,
            slide_index,
            session["slides"],
            session["density"],
            session["difficulty"],
        )

        session["slides"][slide_index] = regenerated_slide

        return json_response(
            {
                "message": "Slide regenerated.",
                "slide_index": slide_index,
                "slide": regenerated_slide,
                "slides": session["slides"],
                "metadata": metadata,
            }
        )
    except InvalidLLMResponseError:
        app.logger.exception("LLM returned invalid JSON during slide regeneration.")
        return json_response({"error": "Invalid LLM response"}, 500)
    except ValueError as error:
        app.logger.warning("Invalid request for /regenerate-slide: %s", error)
        return json_response({"error": str(error) or "Invalid input"}, 400)
    except Exception as error:
        app.logger.exception("Unexpected error in /regenerate-slide")
        return json_response({"error": str(error) or "Something went wrong"}, 500)


@app.get("/download-ppt")
def download_ppt():
    session_id = request.args.get("session_id", "")
    session = SESSION_STORE.get(session_id)
    if not session:
        return json_response({"error": "Session not found. Generate slides before downloading."}, 404)

    ppt_stream = build_presentation(session["slides"], topic_hint=session["topic"])
    filename = f"{slugify_filename(session['topic'])}.pptx"

    return send_file(
        ppt_stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.get("/health")
def health():
    return json_response({"status": "ok"})


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    app.logger.warning("HTTP error: %s", error)
    return json_response({"error": error.description or "Something went wrong"}, error.code or 500)


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.exception("Unhandled server error")
    return json_response({"error": "Something went wrong"}, 500)


if __name__ == "__main__":
    app.run(debug=True)
