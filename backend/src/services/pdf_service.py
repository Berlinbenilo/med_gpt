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
            image_urls.append(f"{SERVER_URL}/{image_id}")
        return image_urls

    @staticmethod
    def crop_figures(layout: lp.Layout, image: np.ndarray):
        Path(IMAGE_PATH).mkdir(parents=True, exist_ok=True)
        figure_blocks = lp.Layout([b for b in layout if b.type == 'figure'])
        image_urls = []
        for i, figure_block in enumerate(figure_blocks):
            x1, y1, x2, y2 = int(figure_block.coordinates[0]), int(figure_block.coordinates[1]), \
                int(figure_block.coordinates[2]), int(figure_block.coordinates[3])
            image_id = str(uuid4())
            cropped_figure = image[y1:y2, x1 - 20:x2 + 20]
            cropped_img = Image.fromarray(cropped_figure)
            cropped_img.save(f'{IMAGE_PATH}/{image_id}.png')
            image_urls.append(f"{SERVER_URL}/{image_id}")
        return image_urls

    def extract_image_detectron(self, page_num: int = 0) -> lp.Layout:
        image = np.asarray(pdf2image.convert_from_path(self.pdf_path)[page_num])
        layout_result = self.model.detect(image)
        image_urls = self.crop_figures(layout_result, image)
        return image_urls


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

    def generate_semantic_chunk(self, batch_size: int = 10):
        file_id = f"{uuid4()}_{datetime.now()}"
        documents = [self.pypdf_extraction.extract_text(page_no) for page_no in range(self.pypdf_extraction.length)]
        semantic_chunker = SemanticChunker(self.embedder, breakpoint_threshold_type="percentile")
        semantic_chunks = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            semantic_chunks.extend(semantic_chunker.create_documents(batch))
            print("Processed batch from index", i, "to", i + batch_size)
        all_semantic_chunks, ids = [], []
        for chunk in semantic_chunks:
            chunk_id = str(uuid4())
            ids.append(chunk_id)
            metadata = {
                "file_id": file_id,
                "chunk_id": chunk_id,
            }
            all_semantic_chunks.append(Document(
                page_content=chunk.page_content,
                metadata=metadata
            ))
            FileIngestion.insert(metadata).execute()
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
