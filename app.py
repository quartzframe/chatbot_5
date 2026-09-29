import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types

from chatbot_config import SYSTEM_PROMPT, MODEL_NAME

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    if client is None:
        return jsonify({
            "error": "Gemini API key is not configured."
        }), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    contents = []

    if isinstance(history, list):
        for item in history[-12:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            text = str(item.get("text", "")).strip()

            if role in {"user", "model"} and text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=text)]
                    )
                )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=1200,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            answer = (
                "I couldn't generate a response right now. "
                "Please try your business question again."
            )

        return jsonify({"answer": answer})

    except Exception:
        app.logger.exception("Gemini API request failed")
        return jsonify({
            "error": "The AI service could not process this request right now."
        }), 502


if __name__ == "__main__":
    app.run()
