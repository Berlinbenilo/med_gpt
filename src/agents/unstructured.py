from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from src.agents.base import BaseAgent
from src.constants.prompts import ALL_PROMPTS
from src.entities.state_model import MedTutorGraphState


class UnstructuredAgent(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "unstructured_search"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        print("Unstructured Agent invoked")

        messages = [("user", self.state['messages'][-1].content)]
        print("type -->",self.state.get('medical_type'))
        if not self.prompt:
            self.prompt = ALL_PROMPTS[self.state.get('medical_type')]

        graph = create_react_agent(self.llm, self.tools, prompt=self.prompt, state_schema=MedTutorGraphState)
        result = await graph.ainvoke({"messages": messages})
        print("__unstructured agent__")
        print(result)
        return Command(update={"messages": [result["messages"][-1].content]}, goto="__end__")

