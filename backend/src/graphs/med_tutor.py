from typing import Dict

from langchain_qdrant import QdrantVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph

from backend.src.agents.classifier import SubjectClassifier
from backend.src.agents.query_preprocessor import QueryPreprocessor
from backend.src.agents.question_type_router import QuestionTypeRouter
from backend.src.agents.unstructured import UnstructuredAgent
from backend.src.constants.prompts import MEDICAL_QUESTION_CLASSIFIER_PROMPT, MEDICAL_QUESTION_ROUTER_PROMPT, \
    SHORT_ANSWER_PROMPT, CASE_STUDIES_PROMPT, QUESTION_REPHRASER_PROMPT
from backend.src.constants.properties import classifier_model
from backend.src.entities.state_model import MedTutorGraphState
from backend.src.services.llm_service import llm_factory
from backend.src.tools.vector_search import VectorSearch

llm_registry = {'deepseek-r1-0528': llm_factory('deepseek-r1-0528'),
                'gpt-4.1': llm_factory('gpt-4.1'),
                'llama4-maverick-instruct-basic': llm_factory('llama4-maverick-instruct-basic'),
                'gemini-2.5-pro-preview-03-25': llm_factory('gemini-2.5-pro-preview-03-25'),
                "deepseek-v3-0324": llm_factory('deepseek-v3-0324')}


class MedTutor(object):
    def __init__(self, collection, model_config=None, session=None):
        self.collection: QdrantVectorStore = collection
        self.builder = StateGraph(MedTutorGraphState)
        self.model_config: Dict = model_config
        self.session = session

        async def unstructured_search(state):
            vector_search_tool = VectorSearch(collection=self.collection)
            return await UnstructuredAgent(state=state, tools=[vector_search_tool],
                                           llm=llm_registry.get(
                                               model_config.get('model_name'))).arun()  # replaced self.model_config

        async def subject_classifier(state):
            print("Subject classifier agent invoked")
            return await SubjectClassifier(state=state, tools=[], llm=llm_registry.get(classifier_model),
                                           prompt=MEDICAL_QUESTION_CLASSIFIER_PROMPT).arun()

        async def query_preprocessor(state):
            return await QueryPreprocessor(state=state, tools=[], llm=llm_registry.get(classifier_model),
                                           prompt=QUESTION_REPHRASER_PROMPT, session_id=self.session).arun()

        async def question_type_router(state):
            return await QuestionTypeRouter(state=state, tools=[], llm=llm_registry.get(classifier_model),
                                            prompt=MEDICAL_QUESTION_ROUTER_PROMPT).arun()

        async def short_answer(state):
            print("Short answer agent invoked")
            vector_search_tool = VectorSearch(collection=self.collection)
            short_answer_agent = UnstructuredAgent(state=state, tools=[vector_search_tool],
                                                   llm=llm_registry.get(model_config.get('model_name')),
                                                   prompt=SHORT_ANSWER_PROMPT)
            short_answer_agent.name = "short_answer"
            return await short_answer_agent.arun()

        async def case_studies(state):
            print("Case studies agent invoked")
            vector_search_tool = VectorSearch(collection=self.collection)
            case_study_agent = UnstructuredAgent(state=state, tools=[vector_search_tool],
                                                 llm=llm_registry.get(model_config.get('model_name')),
                                                 prompt=CASE_STUDIES_PROMPT)
            case_study_agent.name = "case_studies"
            return await case_study_agent.arun()

        self.agents = {
            "query_preprocessor": query_preprocessor,
            "question_type_router": question_type_router,
            "long_answer": subject_classifier,
            "unstructured_search": unstructured_search,
            "short_answer": short_answer,
            "case_studies": case_studies
        }

    def quest_router(self, state):
        print("Routing question type based on state:", state)
        return state['question_type'] if 'question_type' in state else "long_answer"

    def _create_graph(self, memory: MemorySaver = None):
        self.builder.add_node('question_type_router', self.agents['question_type_router'])
        self.builder.add_node('query_preprocessor', self.agents['query_preprocessor'])
        self.builder.add_node('long_answer', self.agents['long_answer'])
        self.builder.add_node('unstructured_search', self.agents['unstructured_search'])
        self.builder.add_node('short_answer', self.agents['short_answer'])
        self.builder.add_node('case_studies', self.agents['case_studies'])

        self.builder.set_entry_point("query_preprocessor")
        self.builder.add_edge(START, "query_preprocessor")
        self.builder.add_edge("query_preprocessor", "question_type_router")

        self.builder.add_conditional_edges(
            "question_type_router",
            self.quest_router,
            {
                "short_answer": "short_answer",
                "long_answer": "long_answer",
                "case_studies": "case_studies"
            }
        )

        self.builder.add_edge("long_answer", "unstructured_search")

        self.builder.add_edge("short_answer", END)
        self.builder.add_edge("unstructured_search", END)
        self.builder.add_edge("case_studies", END)
        app = self.builder.compile(checkpointer=memory)

        graph_plot = app.get_graph().draw_mermaid_png()
        graph_path = f"graph.png"
        with open(graph_path, "wb") as f:
            f.write(graph_plot)
        return app

    async def arun(self, input_payload, memory, config=None):
        app = self._create_graph(memory=memory)
        response = await app.ainvoke(input_payload, config=config)
        return response['messages'][-1]
