from typing import Any, Type, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


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

    def _run(self, query: str, top_k: int = 50, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        results = self.collection.similarity_search(query, k=top_k)
        contents = "\n".join([doc.page_content for doc in results])
        return contents

    async def _arun(self, query: str, top_k: int = 50, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        results = await self.collection.asimilarity_search(query, k=top_k)
        contents = "\n".join([doc.page_content for doc in results])
        return contents
