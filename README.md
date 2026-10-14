# News Category Classifier

A Gradio interface that sends news text to Groq and displays a validated category and model confidence. Categories are World, Sports, Business and Sci/Tech. Blank input is rejected before calling the API; malformed output is reported as a failure.

## Run locally

Use Python with a virtual environment. Install the dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install gradio requests python-dotenv
```

Set GROQ_API_KEY in your local environment before running. Do not commit or share the key. The key can also be stored in a local .env file, but keep that file outside version control.

```sh
python app.py
```

The app opens a browser and creates a temporary public Gradio link. Keep the process running while using it; Control-C stops it. Text is sent to Groq. The configured model must be available to your account. Rate-limit retries respect Retry-After where supplied.

## Limits

The model is forced to pick one of four categories. Non-news input, including a personal name, can receive an unsupported category; only blank input is currently rejected. Self-reported confidence is not a guarantee of accuracy. Avoid confidential input.

This public version contains only the application and this README. Assignment datasets, labels, raw replies, reports, screenshots, certificates, keys and local environments are excluded. The complete course project remains separate.
