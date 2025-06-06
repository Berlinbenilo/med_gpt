import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams
import layoutparser as lp

from src.constants.prompts import RAG_PROMPT
from src.constants.properties import IMAGE_PATH, PDF_PATH

load_dotenv(override=True)
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

print("Loading Qdrant client and initializing collection...")
client = QdrantClient(path="./qdrant_storage", prefer_grpc=True)

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
model = lp.Detectron2LayoutModel(
    'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
    r'/mnt/c/Users/Deepika Ramesh/Downloads/model_final.pth',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={0: "None", 1: "text", 2: "title", 3: "list", 4: "table", 5: "figure"}
)
print("Model Loaded..!")

app = FastAPI()

llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o", temperature=0.0)

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

@app.get("/pdf/{pdf_id}")
def get_image(pdf_id: str):
    file_path = os.path.join(PDF_PATH, f"{pdf_id}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf")
    return {"error": "File not found!"}


@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    temp_path = os.path.join(PDF_PATH, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    from src.services.ingestion import UnstructuredIngestion
    from src.services.extraction import PyPDFExtraction

    pdf_extraction = PyPDFExtraction(temp_path, model=model)
    ingestion_service = UnstructuredIngestion(temp_path, collection=vector_store, pdf_extraction= pdf_extraction)
    result = ingestion_service.ingest()
    return {"message": "PDF ingested successfully", "ids": result.chunk_ids}


@app.post("/search")
async def search(query: str, top_k: int = 10):
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    prompt = PromptTemplate(
        template=RAG_PROMPT,
        input_variables=["question", "context"]
    )
    rag_chain = prompt | llm | StrOutputParser()
    generation = rag_chain.invoke({"context": format_docs(results), "question": query})
    return {
        "results": [doc for doc in results],
        "answer": generation,
    }


if __name__ == "__main__":
    uvicorn.run(app)