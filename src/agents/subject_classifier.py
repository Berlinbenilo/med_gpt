from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from pydantic import BaseModel, Field
from langgraph.graph import END

from src.agents.base import BaseAgent


class Classifier(BaseModel):
    type: str = Field(..., description="category name")
    # message: str = Field(..., description="explanation if non medical user query is provided")


class SubjectClassifier(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "classifier"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        print("Classifier Agent invoked")
        _prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt),
            ("human", "{user_query}"),
        ])
        formatted_prompt = _prompt.format_messages(user_query=self.state['messages'][-1].content)
        bound_llm = self.llm.with_structured_output(Classifier)
        response = bound_llm.invoke(formatted_prompt)
        print("Type --> ",response.type)
        return Command(update={"medical_type": response.type}, goto="unstructured_search")

