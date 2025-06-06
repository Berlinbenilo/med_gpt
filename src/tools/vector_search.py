from typing import Any, Type, Optional

from dotenv import load_dotenv
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams

load_dotenv(override=True)

sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")


client = QdrantClient(path="./qdrant_storage", prefer_grpc=True)

collection_name = "pdf_collection_1"
if collection_name not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name=collection_name,
        vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
        sparse_vectors_config={
            "sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))
        },
    )
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
    sparse_embedding=sparse_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
    vector_name="dense",
    sparse_vector_name="sparse",
)


class VectorSearchInput(BaseModel):
    query: str = Field(description="The search query to find relevant documents in the vector database.")
    top_k: int = Field(default=5, description="Number of top documents to return.")


class VectorSearch(BaseTool):
    name: str = "vector_search"
    description: str = (
        "Search for relevant documents in the vector database based on the provided query. "
        "Returns a list of documents with their content, file names, page numbers, and image URLs."
    )
    args_schema: Type[BaseModel] = VectorSearchInput
    collection: Any

    def _run(self, query: str, top_k: int = 5, run_manager: Optional[CallbackManagerForToolRun] = None) -> Any:
        results = self.collection.similarity_search(query, k=top_k)
        return results

    def _arun(self, query: str, top_k: int = 5, run_manager: Optional[CallbackManagerForToolRun] = None) -> Any:
        results = self.collection.asimilarity_search(query, k=top_k)
        return results

vector_search = VectorSearch(collection=vector_store)