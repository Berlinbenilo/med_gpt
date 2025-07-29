
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

import os, glob

from backend.src.constants.config import vector_store, azure_embedding
from backend.src.constants.properties import PDF_PATH
from backend.src.entities.api_model import PDF
from backend.src.entities.db_model import FileIngestionStatus
from backend.src.services.pdf_service import Extraction, PDFIngestion

router = APIRouter(prefix="/pdf", tags=["PDF"])

@router.get("/{filename}")
def get_pdf(filename: str):
    pdf_path = os.path.join("asserts/pdf", filename)
    if not os.path.exists(pdf_path):
        return {"error": "File not found"}
    return FileResponse(pdf_path, media_type="application/pdf")


@router.post("/ingest/file")
async def ingest_pdf(file: UploadFile = File(...)):
    temp_path = os.path.join(PDF_PATH, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    pdf_extraction = Extraction(temp_path)
    ingestion_service = PDFIngestion(temp_path, collection=vector_store, pdf_extraction=pdf_extraction)
    result = ingestion_service.ingest_chunks()
    return {"message": "PDF ingested successfully", "ids": result.chunk_ids}


@router.post("/ingest/folder")
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
                ingestion_service = PDFIngestion(dest_path, collection=vector_store, pdf_extraction=pdf_extraction,
                                                 embedder=azure_embedding)
                result = ingestion_service.ingest_chunks()
                all_results.append({"file": filename})
            finally:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
        except Exception as e:
            print(repr(e))
            continue
    return {"message": "PDFs ingested successfully", "results": all_results}