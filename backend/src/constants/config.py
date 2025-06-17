import layoutparser as lp
from layoutparser.models import Detectron2LayoutModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams

sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

print("Loading Qdrant client and initializing collection...")
client = QdrantClient(host="localhost", port=6333)
# client = QdrantClient(path="./qdrant_storage", prefer_grpc=True)

collection_name = "pdf_collection"
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
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
    sparse_embedding=sparse_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
    vector_name="dense",
    sparse_vector_name="sparse",
)

print("Embeddings loaded and vector store initialized.")
print("Loading Detectron2 Layout Model...")
detectron_model = Detectron2LayoutModel(
    'C:/Users/Deepika Ramesh/Projects/med_rag/config.yml',
    # r'C:/Users/Deepika Ramesh/Downloads/model_final.pth',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={0: "None", 1: "text", 2: "title", 3: "list", 4: "table", 5: "figure"}
)
print("Model Loaded..!")
