from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent
from backend.src.constants.properties import classifier_model
from backend.src.services.llm_service import llm_factory


class Classifier(BaseModel):
    type: str = Field(..., description="category name")


class SubjectClassifier(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "long_answer"
        self.prompt = prompt

        super().__init__(state, tools, model_config)

    async def arun(self):
        llm = llm_factory(model_name= classifier_model)
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt + "\nUser query: {user_query}",
            llm=llm,
            placeholder_input={"user_query": self.state['messages'][-1].content},
            validator=Classifier
        )
        return Command(update={"medical_type": parsed_response.get('type')}, goto="unstructured_search")
