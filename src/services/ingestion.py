import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
from uuid import uuid4

from langchain_core.documents import Document

from src.constants.properties import SERVER_URL
from src.entities.db_model import File, Image
from src.services.extraction import PyPDFExtraction

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings


@dataclass
class IngestionResult:
    documents: List[Document]
    chunk_ids: List[str]
    success: bool
    error: Optional[str] = None


class UnstructuredIngestion:
    def __init__(self, file_path: str, llm=None, collection=None,
                 pdf_extraction: Optional[PyPDFExtraction] = None,
                 embedder = None):
        self._validate_file(file_path)
        self.pypdf_extraction: PyPDFExtraction = pdf_extraction
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
        return ""

    def _create_ingestion_status(self, chunk_id: str, image_url: str,
                                 page_no: int, status: str) -> None:
        IngestionStatus.create(
            chunk_id=chunk_id,
            image_url=image_url,
            file_name=self.file_name,
            file_path = self.file_path,
            page_no=page_no,
            status=status
        )

    def _process_page(self, page_no: int) -> Tuple[Optional[Document], str]:
        """Process a single page and return document and chunk ID."""
        chunk_id = str(uuid.uuid4())

        try:
            content = self.pypdf_extraction.extract_text(page_no)
            image_urls = self.pypdf_extraction.extract_image_detectron(page_no)

            if image_urls:
                for image_url in image_urls:
                    content += self._extract_image_info(image_url)
                    self._create_ingestion_status(chunk_id, image_url, page_no, "completed")
            else:
                self._create_ingestion_status(chunk_id, "", page_no, "completed")

            document = Document(
                page_content=content,
                metadata={
                    "chunk_id": chunk_id,
                    "file_name": self.file_name,
                    "file_url": f"{SERVER_URL}/{os.path.basename(self.file_name).split('.')[0]}.pdf",
                    "image_urls": image_urls,
                }
            )
            return document, chunk_id

        except Exception as e:
            self._create_ingestion_status(chunk_id, "", page_no, "failed")
            print(f"Error processing page {page_no}: {e}")
            return None, chunk_id

    def format_chunk(self, title: str, content: str, page_no: int, image_url: str, pdf_url: str) -> str:
        chunk = (
            f"# {title}\n"
            f"{content}\n"
            f"page no: {page_no}\n"
            f"image url: {image_url}\n"
            f"pdf url: {pdf_url}"
        )
        return chunk

    def _format_file_content(self) -> Tuple[List[Document], List[str]]:
        """Process all pages and return formatted documents and IDs."""
        documents, ids = [], []

        for page_no in range(self.pypdf_extraction.length):
            document, chunk_id = self._process_page(page_no)
            if document:
                documents.append(document)
                ids.append(chunk_id)
            print(f"Page no {page_no} is processed..!")

        return documents, ids

    def generate_semantic_chunk(self):
        documents = [self.pypdf_extraction.extract_text(page_no) for page_no in range(self.pypdf_extraction.length)]
        semantic_chunker = SemanticChunker(self.embedder, breakpoint_threshold_type="percentile")
        semantic_chunks = semantic_chunker.create_documents(documents)
        all_semantic_chunks, ids = [], []
        for chunk in semantic_chunks:
            chunk_id = str(uuid4())
            ids.append(chunk_id)
            metadata = {
                "file_name": self.file_name,
                "file_url": f"{SERVER_URL}/pdf/{self.file_name}",
                "chunk_id": chunk_id
            }
            all_semantic_chunks.append(Document(
                page_content=chunk.page_content,
                metadata=metadata
            ))
            File.insert(metadata)
        return all_semantic_chunks, ids


    def ingest(self) -> IngestionResult:
        if self.collection is None:
            raise ValueError("Collection is not initialized")
        documents, ids = self.generate_semantic_chunk()

        if not documents:
            return IngestionResult([], [], False, "No documents to ingest")

        self.collection.add_documents(documents, ids=ids)
        print(f"Ingested {len(documents)} documents into the collection")

        return IngestionResult(documents, ids, True)
