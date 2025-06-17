from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent


class Classifier(BaseModel):
    type: str = Field(..., description="category name")


class SubjectClassifier(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "classifier"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        print("Classifier Agent invoked")
        # _prompt = ChatPromptTemplate.from_messages([
        #     ("system", self.prompt),
        #     ("human", "{user_query}"),
        # ])
        # formatted_prompt = _prompt.format_messages(user_query=self.state['messages'][-1].content)
        # bound_llm = self.llm.with_structured_output(Classifier)
        # response = bound_llm.invoke(formatted_prompt)
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt + "\nUser query: {user_query}",
            placeholder_input={"user_query": self.state['messages'][-1].content},
            validator=Classifier
        )
        return Command(update={"medical_type": parsed_response.get('type')}, goto="unstructured_search")
