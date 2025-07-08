import os

from dotenv import load_dotenv
load_dotenv(override=True)

IMAGE_PATH = "asserts/images"
PDF_PATH = "asserts/pdf"

SERVER_URL = "http://localhost:8000"


model_config = {
    "gpt-4.1": {
        'temperature': 0,
        "model": "gpt-4.1",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "gpt-4o": {
        'temperature': 0,
        "model": "gpt-4o",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "o3-mini": {
        "model": "o3-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "deepseek-v3-0324":{
        "model": "accounts/fireworks/models/deepseek-v3-0324",
        "base_url":"https://api.fireworks.ai/inference/v1",
           "api_key": os.getenv("FIREWORKS_API_KEY"),
    },
    "llama4-maverick-instruct-basic":{
        "model": "accounts/fireworks/models/llama4-maverick-instruct-basic",
        "base_url":"https://api.fireworks.ai/inference/v1",
           "api_key": os.getenv("FIREWORKS_API_KEY"),
    }
}
