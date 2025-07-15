import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import layoutparser as lp
import numpy as np
import pdf2image
from PIL import Image
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

from backend.src.constants.properties import IMAGE_PATH, SERVER_URL
from backend.src.entities.db_model import FileIngestion, FileIngestionStatus


@dataclass
class IngestionResult:
    documents: List[Document]
    chunk_ids: List[str]
    success: bool
    error: Optional[str] = None


class Extraction(object):
    def __init__(self, pdf_path: str, model: lp.Detectron2LayoutModel = None):
        self.pdf_path = pdf_path
        self.reader = PdfReader(self.pdf_path)
        self.length = len(self.reader.pages)
        self.model = model
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

    @staticmethod
    def crop_figures(figure_blocks, image: np.ndarray):
        image_urls = []
        height, width = image.shape[:2]

        for i, figure_block in enumerate(figure_blocks):
            # Get coordinates and ensure they're within image bounds
            x1 = max(0, int(figure_block.coordinates[0]))
            y1 = max(0, int(figure_block.coordinates[1]))
            x2 = min(width, int(figure_block.coordinates[2]))
            y2 = min(height, int(figure_block.coordinates[3]))

            if x1 < x2 and y1 < y2:
                image_id = str(uuid4())
                cropped_figure = image[y1:y2, x1:x2]
                cropped_img = Image.fromarray(cropped_figure)

                cropped_img.save(f'{IMAGE_PATH}/{image_id}.png')
                image_urls.append(f"{SERVER_URL}/{image_id}")

        return image_urls

    def generate_context_summary(self, image_path: Path, llm) -> str:
        pass

    def detect_and_generate_context(
            self,
            page_number: int = 0,
            image_path: str = "assets/images",
            context_summary: bool = False,
            poppler_path: str = r"C:\poppler-24.08.0\Library\bin"
    ) -> List[Document]:
        """Detect figures in PDF pages and generate context summaries.

        Args:
            page_number: Page to process (0 for all pages)
            image_path: Directory to save extracted images
            context_summary: Whether to generate context summaries
            poppler_path: Path to poppler binaries
        """
        convert_kwargs = {
            "pdf_path": self.pdf_path,
            "poppler_path": poppler_path
        }

        if page_number:
            convert_kwargs.update({
                "first_page": page_number,
                "last_page": page_number
            })

        pages = pdf2image.convert_from_path(**convert_kwargs)
        documents = []
        Path(image_path).mkdir(parents=True, exist_ok=True)

        for page_idx, page in enumerate(pages):
            layout_result = self.model.detect(np.array(page))
            figure_blocks = lp.Layout([b for b in layout_result if b.type == 'figure'])

            if figure_blocks:
                image_name = f"page_{page_number or page_idx}_{uuid4()}"
                image_path_full = Path(image_path) / f"{image_name}.png"
                page.save(image_path_full)

                # Extract figures if needed
                # image_urls = self.crop_figures(figure_blocks, np.array(page))

                if context_summary:
                    documents.append(Document(
                        page_content=self.generate_context_summary(image_path_full),
                        metadata={
                            "image_urls": f"{SERVER_URL}/image/{image_name}",
                        }
                    ))

        return documents


class Ingestion:
    def __init__(self, file_path: str, llm=None, collection=None,
                 pdf_extraction: Optional[Extraction] = None,
                 embedder=None):
        self._validate_file(file_path)
        self.pypdf_extraction: Extraction = pdf_extraction
        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.llm = llm
        self.collection = collection
        self.embedder = embedder or OpenAIEmbeddings()

    @staticmethod
    def _validate_file(file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        if not os.path.isfile(file_path):
            raise ValueError(f"{file_path} is not a valid file.")

    def _extract_image_info(self, image_url: str) -> str:
        """Extract information from image using LLM (placeholder)."""
        # TODO: Implement image summarization logic
        ...

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
            print(f"Processing pages {start_page} to {end_page} (batch {batch_num})")

            for doc, chunk_id in process_chunks(text_batch):
                all_semantic_chunks.append(doc)
                ids.append(chunk_id)

            del text_batch

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
