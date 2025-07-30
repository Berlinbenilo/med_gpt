import hashlib
from typing import Dict, List, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from pydantic import BaseModel

from backend.src.constants.properties import model_config


def get_model(model_name: str) -> Tuple[Dict, str]:
    try:
        print("get Selected model:", model_name)
        # res = Models.get(Models.name == model_name)
        # return model_config[res.name], res.model_provider
        models = {'deepseek-r1-0528': "fireworks",
                'gpt-4.1': "azure",
                'llama4-maverick-instruct-basic': "fireworks",
                'gemini-2.5-pro': "google",
                "deepseek-v3-0324": "fireworks"}
        return model_config[model_name], models[model_name]

    except IndexError:
        raise ValueError(
            f"Model {model_name} not found in the database. Please ensure it is registered before running the application.")


def llm_factory(model_name, stream = False) -> BaseChatModel:
    model = None
    config, model_provider = get_model(model_name)
    print(f"Using model: {model_name} with provider: {model_provider} and config: {config}")
    if model_provider == "openai" or model_provider == "fireworks":
        model = ChatOpenAI(**config, streaming= stream)
    if model_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = ChatGoogleGenerativeAI(**config)
    if model_provider == "azure":
        model = AzureChatOpenAI(**config, streaming= stream)
    return model


class LLMWrapper(object):
    def __init__(self, model_name=None, llm=None, tools: List = None):
        self.llm = llm if llm else llm_factory(model_name)
        self.tools = tools
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)

    def invoke_with_parser(self, prompt_template: str, llm=None, placeholder_input: Dict = None,
                           validator: Optional[BaseModel] = None,
                           stream: bool = False):
        _parser = JsonOutputParser(pydantic_object=validator) if validator else StrOutputParser()

        prompt = PromptTemplate.from_template(
            template=prompt_template,
            partial_variables={"format_instructions": _parser.get_format_instructions() if validator else ""},
        )
        llm = llm if llm else self.llm
        chain = prompt | llm | _parser

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
