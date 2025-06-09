import os

from dotenv import load_dotenv

from src.constants.prompts import ANATOMY_ESSAY_PROMPT

load_dotenv(override=True)

IMAGE_PATH = "asserts/images"
PDF_PATH = "asserts/pdf"

SERVER_URL = "http://localhost:8000"

available_model = {
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "ollama": ["llama3"]
}

model_config = {
    "gpt-4o-mini": {
        'temperature': 0,
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "gpt-4o": {
        'temperature': 0,
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "llama3": {
        'temperature': 0,
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }
}
