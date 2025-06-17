from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from backend.src.agents.base import BaseAgent
from backend.src.constants.prompts import ALL_PROMPTS
from backend.src.entities.state_model import MedTutorGraphState


class UnstructuredAgent(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "unstructured_search"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        print("Unstructured Agent invoked")

        messages = [("user", self.state['messages'][-1].content)]
        print("type -->", self.state.get('medical_type'))
        if not self.prompt:
            self.prompt = ALL_PROMPTS[self.state.get('medical_type')]

        if self.tools:
            self.parser_obj.llm = self.parser_obj.llm.bind_tools(self.tools)

        graph = create_react_agent(self.parser_obj.llm, self.tools, prompt=self.prompt, state_schema=MedTutorGraphState)
        result = await graph.ainvoke({"messages": messages})
        return Command(update={"messages": [result["messages"][-1].content]}, goto="__end__")
