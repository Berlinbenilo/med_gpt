import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams

load_dotenv(override=True)

azure_embedding = AzureOpenAIEmbeddings(
    model="text-embedding-ada-002",  # Can specify model with new text-embedding-3 models
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_EMBED"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBED"),
    api_version=os.getenv("OPENAI_API_VERSION_EMBED"),
)

sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

print("Loading Qdrant client and initializing collection...")
client = QdrantClient(host=os.getenv("QDRANT_HOST"), port=int(os.getenv("QDRANT_PORT", 6333)))
print(os.getenv("QDRANT_HOST"))
collection_name = "pdf_collection-7963541598217832"
if collection_name not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name=collection_name,
        vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
        sparse_vectors_config={
            "sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))
        },
    )
print("Initialized Qdrant client and collection.")
print("Loading embeddings...")
huggingface_embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("Initializing vector store...")
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=huggingface_embedder,
    sparse_embedding=sparse_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
    vector_name="dense",
    sparse_vector_name="sparse",
)
