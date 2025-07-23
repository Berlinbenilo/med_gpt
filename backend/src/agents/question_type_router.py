from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent
from backend.src.constants.properties import classifier_model
from backend.src.services.llm_service import llm_factory


class QuestionType(BaseModel):
    question_type: str = Field(..., description="Type of the question e.g. short_answer, long_answer, use_cases, etc.")


class QuestionTypeRouter(BaseAgent):
    def __init__(self, state, tools, model_config, prompt=None):
        self.name = "question_type_router"
        self.prompt = prompt
        super().__init__(state, tools, model_config)

    async def arun(self):
        llm = llm_factory(model_name= classifier_model)
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt,
            llm=llm,
            placeholder_input={"user_query": self.state['messages'][-1].content},
            validator=QuestionType
        )
        self.state['question_type'] = parsed_response.get('question_type')
        return Command(update={"question_type": parsed_response.get('question_type')},
                       goto=parsed_response.get('question_type'))
