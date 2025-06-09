from src.services.llm_service import llm_factory


class BaseAgent:
    def __init__(self, state, tools, model_config):
        self.name = getattr(self, 'name', 'base_agent')
        self.tools = tools
        self.state = state
        self.llm = llm_factory(model_name=model_config.get('model_name', 'gpt-4o'))

    async def arun(self):
        raise NotImplementedError("Subclasses must implement the arun method.")
