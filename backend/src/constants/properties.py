import os

from dotenv import load_dotenv
load_dotenv(override=True)

IMAGE_PATH = "asserts/images"
PDF_PATH = "asserts/pdf"

SERVER_URL = "http://localhost:8000"


model_config = {
    "gpt-4o-mini": {
        'temperature': 0,
        "model": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "gpt-4o": {
        'temperature': 0,
        "model": "gpt-4o",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "llama3": {
        'temperature': 0,
        "model": "llama3",
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    },
    "claude-3-7-sonnet-latest": {
        'temperature': 0,
        "model": "claude-3-7-sonnet-latest",
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
    },
    "gemini-2.0-flash": {
        'temperature': 0,
        "model": "gemini-2.0-flash",
        "api_key": os.getenv("GOOGLE_API_KEY"),
    },
    "deepscaler:1.5b": {
        'temperature': 0,
        "model": "deepscaler:1.5b",
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    },
}
