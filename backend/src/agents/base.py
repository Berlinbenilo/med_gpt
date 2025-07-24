from backend.src.services.llm_service import LLMWrapper


class BaseAgent:
    def __init__(self, state, tools, llm=None):
        self.name = getattr(self, 'name', 'base_agent')
        self.tools = tools
        self.state = state
        self.llm = llm
        self.parser_obj = LLMWrapper(llm=self.llm)

    async def arun(self):
        raise NotImplementedError("Subclasses must implement the arun method.")
