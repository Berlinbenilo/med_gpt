import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from PyPDF2 import PdfReader
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker

from backend.src.constants.properties import IMAGE_PATH, SERVER_URL
from backend.src.entities.db_model import FileIngestion, FileIngestionStatus


@dataclass
class IngestionResult:
    documents: List[Document]
    chunk_ids: List[str]
    success: bool
    error: Optional[str] = None


class Extraction(object):
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.reader = PdfReader(self.pdf_path)
        self.length = len(self.reader.pages)
        print(f"NO of pages : {self.length}")

    def extract_text(self, page_num: int) -> str:
        page = self.reader.pages[page_num]
        return page.extract_text()

    def extract_image(self, page_num: int) -> List[str]:
        page = self.reader.pages[page_num]
        image_urls = []

        Path(IMAGE_PATH).mkdir(parents=True, exist_ok=True)
        for count, image_file_object in enumerate(page.images):
            image_id = str(uuid4())
            with open(f"{IMAGE_PATH}/{image_id}.png", "wb") as fp:
                fp.write(image_file_object.data)
            image_urls.append(f"{SERVER_URL}/images/{image_id}")
        return image_urls


class PDFIngestion:
    def __init__(self, file_path: str, llm=None, collection=None,
                 pdf_extraction: Optional[Extraction] = None,
                 embedder=None):
        self._validate_file(file_path)
        self.pypdf_extraction: Extraction = pdf_extraction
        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.llm = llm
        self.collection = collection
        self.embedder = embedder

    @staticmethod
    def _validate_file(file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        if not os.path.isfile(file_path):
            raise ValueError(f"{file_path} is not a valid file.")

    def generate_semantic_chunk(self, batch_size: int = 30):
        file_id = f"{uuid4()}_{datetime.now()}"
        semantic_chunker = SemanticChunker(self.embedder, breakpoint_threshold_type="percentile")

        def page_text_generator():
            """Generator for page text processing"""
            current_batch = []
            batch_number = 0
            for page_no in range(self.pypdf_extraction.length):
                current_batch.append((page_no, self.pypdf_extraction.extract_text(page_no)))

                if len(current_batch) >= batch_size:
                    yield batch_number, current_batch
                    batch_number += 1
                    current_batch = []

            if current_batch:  # Yield remaining pages
                yield batch_number, current_batch

        def process_chunks(text_batch):
            """Process a batch of text into chunks"""
            # Extract just the text, keeping page numbers separate
            texts = [text for _, text in text_batch]
            chunks = semantic_chunker.create_documents(texts)
            for chunk in chunks:
                chunk_id = str(uuid4())
                metadata = {
                    "file_id": file_id,
                    "chunk_id": chunk_id,
                }

                FileIngestion.insert(metadata).execute()

                document = Document(
                    page_content=chunk.page_content,
                    metadata=metadata
                )
                yield document, chunk_id

        all_semantic_chunks, ids = [], []
        for batch_num, text_batch in page_text_generator():
            start_page = text_batch[0][0]  # First page number in batch
            end_page = text_batch[-1][0]  # Last page number in batch
            for doc, chunk_id in process_chunks(text_batch):
                all_semantic_chunks.append(doc)
                ids.append(chunk_id)

            del text_batch
            print(f"Processed pages {start_page} to {end_page} (batch {batch_num})")

        FileIngestionStatus.insert({
            "file_id": file_id,
            "file_name": self.file_name,
            "file_url": f"{SERVER_URL}/pdf/{self.file_name}",
            "status": "completed"
        }).execute()

        print("File ingestion done successfully for file:", self.file_name)
        return all_semantic_chunks, ids

    def ingest_chunks(self) -> IngestionResult:
        if self.collection is None:
            raise ValueError("Collection is not initialized")
        documents, ids = self.generate_semantic_chunk()

        if not documents:
            return IngestionResult([], [], False, "No documents to ingest")

        self.collection.add_documents(documents, ids=ids)
        print(f"Ingested {len(documents)} documents into the collection")

        return IngestionResult(documents, ids, True)
