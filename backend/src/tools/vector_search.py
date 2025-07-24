from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool, ArgsSchema
from pydantic import BaseModel, Field


class VectorSearchInput(BaseModel):
    query: str = Field(description="The search query to find relevant documents in the vector database.")
    top_k: int = Field(default=50, description="Number of top documents to return.")


class VectorSearch(BaseTool):
    name: str = "vector_search"
    description: str = (
        "REQUIRED: Use this tool to search for relevant information in the vector database. "
        "This tool MUST be used for all user queries that require information retrieval. Always use this tool "
        "Input: query (string) - the search query, top_k (int) - number of results to return."
    )
    args_schema: Optional[ArgsSchema] = VectorSearchInput
    collection: Any

    def _run(self, query: str, top_k: int = 50, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        results = self.collection.similarity_search(query, k=50)
        contents = "\n".join([doc.page_content for doc in results])
        return contents

    async def _arun(self, query: str, top_k: int = 50,
                    run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        results = await self.collection.asimilarity_search(query, k=50)
        contents = "\n".join([doc.page_content for doc in results])
        return contents
