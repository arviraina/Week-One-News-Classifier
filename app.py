import json
import math
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = "openai/gpt-oss-20b"
CATEGORIES = {"World", "Sports", "Business", "Sci/Tech"}

OUTPUT_RULE = """
Return only a JSON object with:
"label": one of World, Sports, Business, Sci/Tech
"confidence": a number between 0 and 1.
"""

PROMPTS = {
    "specific": """
Classify the news into exactly one category.
World: international news, politics, conflict, disasters, national affairs.
Sports: matches, results, athletes, teams, transfers, tournaments.
Business: companies, markets, earnings, economy, trade, jobs, deals.
Sci/Tech: science, research, technology, software, space, health research.

Apply these boundary rules in order:
1. Foreign company earnings or currency moves are Business, not World.
2. Broadcasting rights deals or club finances are Business, not Sports.
3. Technical capability is Sci/Tech; commercial impact is Business.
4. If two categories fit, choose what the item is mostly about.
""" + OUTPUT_RULE,
    "vague": """
What category is this news item? Pick one.
World, Sports, Business, Sci/Tech.
""" + OUTPUT_RULE,
}


def retry_delay(value):
    if not value:
        return 60
    try:
        return max(4, float(value))
    except ValueError:
        try:
            deadline = parsedate_to_datetime(value)
            return max(
                4,
                (deadline - datetime.now(timezone.utc)).total_seconds(),
            )
        except (ValueError, TypeError, OverflowError):
            return 60


def ask_model(prompt, text):
    for attempt in range(3):
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": MODEL,
                "messages": [{
                    "role": "user",
                    "content": prompt + "\nNews item:\n" + text,
                }],
                "temperature": 0,
                "max_completion_tokens": 1024,
            },
            timeout=60,
        )
        if response.status_code == 429 and attempt < 2:
            wait = retry_delay(response.headers.get("Retry-After"))
            print(f"Rate limit: waiting {wait:.0f} seconds.")
            time.sleep(wait)
            continue
        if not response.ok:
            raise RuntimeError(f"HTTP {response.status_code}")
        return response.json()["choices"][0]["message"]["content"]
    raise RuntimeError("Retries exhausted")


def validate(raw):
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("Reply is not a JSON object")
    if result.get("label") not in CATEGORIES:
        raise ValueError("Invalid or missing label")
    confidence = result.get("confidence")
    if (
        type(confidence) not in (int, float)
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        raise ValueError("Invalid or missing confidence")
    return result["label"], confidence


def classify_checked(text):
    # The fix: reject empty input instead of asking AI to guess.
    if not text.strip():
        raise ValueError("Empty input: enter a news item.")
    if not API_KEY:
        raise RuntimeError("Missing Groq key")
    raw = ask_model(PROMPTS["specific"], text)
    label, confidence = validate(raw)
    return raw, label, confidence


import gradio as gr

def classify_news(text):
    try:
        _, label, confidence = classify_checked(text)
        return label, f"{confidence:.2f}"
    except ValueError:
        if not text.strip():
            raise gr.Error("Enter a news item before submitting.")
        raise gr.Error("The AI returned an invalid answer. Please try again.")
    except (RuntimeError, requests.RequestException):
        raise gr.Error("The AI service could not complete the request.")
    finally:
        # Space requests when multiple submissions are queued.
        time.sleep(4)


demo = gr.Interface(
    fn=classify_news,
    inputs=gr.Textbox(
        label="News item",
        placeholder="Enter a headline or short news article",
        lines=5,
    ),
    outputs=[
        gr.Textbox(label="Category"),
        gr.Textbox(label="Model confidence"),
    ],
    title="News Category Classifier",
    description=(
        "Classify news as World, Sports, Business, or Sci/Tech. "
        "Text is sent to Groq for classification. "
        "The model's confidence does not guarantee correctness."
    ),
    api_name="classify",
    concurrency_limit=1,
)

if __name__ == "__main__":
    demo.queue().launch(share=True, inbrowser=True)