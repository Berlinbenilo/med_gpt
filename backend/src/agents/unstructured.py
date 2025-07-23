from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from backend.src.agents.base import BaseAgent
from backend.src.constants.prompts import ALL_PROMPTS


class UnstructuredAgent(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "unstructured_search"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        messages = [("user", self.state['messages'][-1].content)]

        if not self.prompt:
            self.prompt = ALL_PROMPTS[self.state.get('medical_type')]
        agent = create_react_agent(self.parser_obj.llm, self.tools, debug=True, prompt=self.prompt)
        result = await agent.ainvoke({"messages": messages})
        return Command(update={"messages": [result["messages"][-1].content]}, goto="__end__")
