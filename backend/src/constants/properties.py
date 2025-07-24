import os

from dotenv import load_dotenv

load_dotenv(override=True)

IMAGE_PATH = "asserts/images"
PDF_PATH = "asserts/pdf"

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
classifier_model = "deepseek-v3-0324"

model_config = {
    "deepseek-v3-0324": {
        "model": "accounts/fireworks/models/deepseek-v3-0324",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "llama4-maverick-instruct-basic": {
        "model": "accounts/fireworks/models/llama4-maverick-instruct-basic",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "deepseek-r1-0528": {
        "model": "accounts/fireworks/models/deepseek-r1-0528",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "gemini-2.0-flash": {
        "model": "gemini-2.0-flash",
        "api_key": os.getenv("GOOGLE_API_KEY"),
    },
    "gemini-2.5-pro-preview-03-25": {
        "model": "gemini-2.5-pro-preview-03-25",
        "api_key": os.getenv("GOOGLE_API_KEY"),
    },
    "gpt-4.1": {
        'temperature': 0,
        "model": "gpt-4.1",
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_CHAT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_CHAT"),
        "api_version": "2024-12-01-preview",
    },
    "o3-mini": {
        "model": "o3-mini",
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_CHAT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_CHAT"),
        "api_version": "2024-12-01-preview",
    },
    "o4-mini": {
        "model": "o4-mini",
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_CHAT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_CHAT"),
        "api_version": "2024-12-01-preview",
    },
}
