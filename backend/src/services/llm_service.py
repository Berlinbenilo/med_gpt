import hashlib
from typing import Dict, List, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from backend.src.constants.properties import model_config
from backend.src.entities.db_model import Models


def get_model(model_name: str) -> Tuple[Dict, str]:
    try:
        res = Models.get(Models.name == model_name)
        return model_config[res.name], res.model_provider
    except IndexError:
        raise ValueError(f"Model {model_name} not found in the database. Please ensure it is registered before running the application.")


def llm_factory(model_name) -> BaseChatModel:
    print("Selected model name ->", model_name)
    model = None
    config, model_provider = get_model(model_name)
    if model_provider == "openai" or model_provider == "fireworks":
        model = ChatOpenAI(**config)
    return model


class LLMWrapper(object):
    def __init__(self, model_name, tools: List = None):
        self.llm = llm_factory(model_name=model_name)
        self.tools = tools
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

    def invoke_with_parser(self, prompt_template: str, placeholder_input: Dict = None,
                           validator: Optional[BaseModel] = None,
                           stream: bool = False):
        _parser = JsonOutputParser(pydantic_object=validator) if validator else StrOutputParser()

        prompt = PromptTemplate.from_template(
            template=prompt_template,
            partial_variables={"format_instructions": _parser.get_format_instructions() if validator else ""},
        )
        chain = prompt | self.llm | _parser

        if stream:
            return self._invoke_streaming(chain, placeholder_input or {})
        parsed_response = chain.invoke(placeholder_input or {})
        return parsed_response

    @staticmethod
    async def _invoke_streaming(chain, input_data: Dict):
        response_generator = chain.astream(input_data)
        async for partial_response in response_generator:
            yield partial_response


def generate_hash(*args):
    return hashlib.md5("_".join(args).encode()).hexdigest()
