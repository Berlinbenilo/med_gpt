import warnings

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core._api.deprecation import LangChainDeprecationWarning
from backend.src.apis import chat_router, image_router, file_router, model_router, session_router

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router.router)
app.include_router(file_router.router)
app.include_router(chat_router.router)
app.include_router(session_router.router)
app.include_router(model_router.router)

if __name__ == "__main__":
    uvicorn.run(app)
