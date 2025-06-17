from backend.src.services.llm_service import LLMWrapper


class BaseAgent:
    def __init__(self, state, tools, model_config):
        self.name = getattr(self, 'name', 'base_agent')
        self.tools = tools
        self.state = state
        self.parser_obj = LLMWrapper(model_name=model_config.get('model_name', 'gpt-4o'))

    async def arun(self):
        raise NotImplementedError("Subclasses must implement the arun method.")
