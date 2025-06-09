from typing import Dict

from langchain_qdrant import QdrantVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph

from src.agents.unstructured import UnstructuredAgent
from src.agents.subject_classifier import SubjectClassifier
from src.constants.prompts import MEDICAL_QUESTION_CLASSIFIER_PROMPT
from src.entities.state_model import MedTutorGraphState
from src.tools.vector_search import VectorSearch


class MedTutor(object):
    def __init__(self, collection, model_config=None):
        self.collection: QdrantVectorStore = collection
        self.builder = StateGraph(MedTutorGraphState)
        self.model_config: Dict = model_config

        async def unstructured_search(state):
            vector_search_tool = VectorSearch(collection=self.collection)
            return await UnstructuredAgent(state=state, tools=[vector_search_tool],
                                           model_config=self.model_config).arun()

        async def subject_classifier(state):
            return await SubjectClassifier(state=state, tools = [], model_config=self.model_config, prompt= MEDICAL_QUESTION_CLASSIFIER_PROMPT).arun()

        self.agents = {
            "classifier": subject_classifier,
            "unstructured_search": unstructured_search
        }

    def _create_graph(self, memory: MemorySaver = None):
        self.builder.add_node('unstructured_search', self.agents['unstructured_search'])
        self.builder.add_node('classifier', self.agents['classifier'])

        self.builder.set_entry_point("classifier")
        self.builder.add_edge(START, "classifier")
        self.builder.add_edge("classifier", "unstructured_search")
        self.builder.add_edge("unstructured_search", END)

        app = self.builder.compile(checkpointer=memory)
        return app

    async def arun(self, input_payload, memory, config=None):
        app = self._create_graph(memory=memory)
        response = await app.ainvoke(input_payload, config=config)
        return response['messages'][-1]
