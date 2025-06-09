import glob
import os

import uvicorn
from fastapi import FastAPI
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from src.constants.config import vector_store, detectron_model
from src.constants.prompts import RAG_PROMPT
from src.constants.properties import IMAGE_PATH, PDF_PATH, model_config
from src.graphs.med_tutor import MedTutor
from src.services.llm_service import llm_factory
from src.services.pdf_service import Extraction, Ingestion
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class PDF(BaseModel):
    folder_path: str

class Chat(BaseModel):
    input_query: str
    config : Dict

def format_docs(docs):
    return "\n\n".join(
        [
            f'<document>{doc.page_content}</document>'
            for doc, score in docs
        ]
    )


@app.get("/images/{image_id}")
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


@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    temp_path = os.path.join(PDF_PATH, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    pdf_extraction = Extraction(temp_path, model=detectron_model)
    ingestion_service = Ingestion(temp_path, collection=vector_store, pdf_extraction=pdf_extraction)
    result = ingestion_service.ingest_chunks()
    return {"message": "PDF ingested successfully", "ids": result.chunk_ids}


@app.post("/ingest/folder")
async def ingest_folder(pdf_item: PDF):
    dest_folder = os.path.join("asserts", "pdf")
    os.makedirs(dest_folder, exist_ok=True)
    pdf_files = glob.glob(f"{pdf_item.folder_path}/*.pdf")
    all_results = []
    for i, pdf_file in enumerate(pdf_files):
        dest_path = os.path.join(dest_folder, os.path.basename(pdf_file))
        if not os.path.exists(dest_path):
            with open(pdf_file, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
        pdf_extraction = Extraction(dest_path, model=detectron_model)
        ingestion_service = Ingestion(dest_path, collection=vector_store, pdf_extraction=pdf_extraction)
        result = ingestion_service.ingest_chunks()
        all_results.append({"file": os.path.basename(dest_path), "ids": result.chunk_ids})
    return {"message": "All PDFs ingested successfully", "results": all_results}


@app.post("/search")
async def search(query: str, model_name: str, top_k: int = 10):
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    prompt = PromptTemplate(
        template=RAG_PROMPT,
        input_variables=["question", "context"]
    )
    llm = llm_factory(model_name= model_name)
    rag_chain = prompt | llm | StrOutputParser()
    generation = rag_chain.invoke({"context": format_docs(results), "question": query})
    return {
        "results": [doc for doc in results],
        "answer": generation,
    }


@app.post("/chat")
async def chat(item: Chat):
    state = {
        "messages": [HumanMessage(content= item.input_query)],
        "model_config": item.config,
        "remaining_steps": 5
    }
    graph = MedTutor(collection=vector_store, model_config=item.config)
    response = await graph.arun(input_payload=state,
                                      config={"configurable": {"thread_id": "3"}},
                                      memory=MemorySaver()
                                      )
    return {"message" : response, "status" : True}


if __name__ == "__main__":
    uvicorn.run(app)
