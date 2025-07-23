import glob
import os
import warnings
from typing import Dict, List

import uvicorn
from fastapi import FastAPI
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from backend.src.constants.config import vector_store, azure_embedding
from backend.src.constants.prompts import RAG_PROMPT
from backend.src.constants.properties import IMAGE_PATH, PDF_PATH, classifier_model
from backend.src.entities.db_model import Models, FileIngestionStatus
from backend.src.graphs.med_tutor import MedTutor
from backend.src.services.llm_service import llm_factory
from backend.src.services.pdf_service import Extraction, PDFIngestion

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://376fa87969f6.ngrok-free.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PDF(BaseModel):
    folder_path: str


class Chat(BaseModel):
    input_query: str
    config: Dict


def format_docs(docs):
    return "\n\n".join(
        [
            f'<document>{doc.page_content}</document>'
            for doc, score in docs
        ]
    )


@app.get("/image/{image_id}")
def get_image(image_id: str):
    file_path = os.path.join(IMAGE_PATH, f"{image_id}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    return {"error": "File not found!"}


@app.get("/pdf/{filename}")
def get_pdf(filename: str):
    pdf_path = os.path.join("asserts/pdf", filename)
    if not os.path.exists(pdf_path):
        return {"error": "File not found"}
    return FileResponse(pdf_path, media_type="application/pdf")


@app.post("/pdf/ingest/file")
async def ingest_pdf(file: UploadFile = File(...)):
    temp_path = os.path.join(PDF_PATH, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    pdf_extraction = Extraction(temp_path)
    ingestion_service = PDFIngestion(temp_path, collection=vector_store, pdf_extraction=pdf_extraction)
    result = ingestion_service.ingest_chunks()
    return {"message": "PDF ingested successfully", "ids": result.chunk_ids}


@app.post("/pdf/ingest/folder")
async def ingest_folder(pdf_item: PDF):
    dest_folder = os.path.join("asserts", "pdf")
    os.makedirs(dest_folder, exist_ok=True)
    pdf_files = glob.glob(f"{pdf_item.folder_path}/*.pdf")
    all_results = []

    for pdf_file in pdf_files:
        try:
            filename = os.path.basename(pdf_file)
            print(f"Processing file : {filename}")
            if FileIngestionStatus.select().where(FileIngestionStatus.file_name == filename).exists():
                print(f"Skipped : {filename}")
                continue

            dest_path = os.path.join(dest_folder, filename)
            if not os.path.exists(dest_path):
                with open(pdf_file, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())
            try:
                pdf_extraction = Extraction(dest_path)
                ingestion_service = PDFIngestion(dest_path, collection=vector_store, pdf_extraction=pdf_extraction, embedder=azure_embedding)
                result = ingestion_service.ingest_chunks()
                all_results.append({"file": filename})
            finally:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
        except Exception as e:
            print(repr(e))
            continue
    return {"message": "PDFs ingested successfully", "results": all_results}


@app.post("/search")
async def search(query: str, model_name: str, top_k: int = 10):
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    prompt = PromptTemplate(
        template=RAG_PROMPT,
        input_variables=["question", "context"]
    )
    llm = llm_factory(model_name=model_name)
    rag_chain = prompt | llm | StrOutputParser()
    generation = rag_chain.invoke({"context": format_docs(results), "question": query})
    return {
        "results": [doc for doc in results],
        "answer": generation,
    }


@app.post("/chat")
async def chat(item: Chat):
    state = {
        "messages": [HumanMessage(content=item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }
    graph = MedTutor(collection=vector_store, model_config=item.config)
    response = await graph.arun(input_payload=state,
                                config={"configurable": {"thread_id": "1"}},
                                memory=MemorySaver()
                                )
    return {"message": response.content, "status": True}


@app.get("/models")
async def get_models():
    return {
        "models": list(Models.select(Models.id, Models.name).where(Models.name != classifier_model).dicts())
    }


if __name__ == "__main__":
    uvicorn.run(app)
