from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent


class Classifier(BaseModel):
    type: str = Field(..., description="category name")


class SubjectClassifier(BaseAgent):
    def __init__(self, state, tools, llm, prompt=None):
        self.name = "long_answer"
        self.prompt = prompt

        super().__init__(state, tools, llm)

    async def arun(self):
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt + "\nUser query: {user_query}",
            llm=self.llm,
            placeholder_input={"user_query": self.state['messages'][-1].content},
            validator=Classifier
        )
        print("Parsed response from classifier:", parsed_response)
        return Command(update={"medical_type": parsed_response.get('type')}, goto="unstructured_search")
