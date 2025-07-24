from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent


class QuestionType(BaseModel):
    question_type: str = Field(..., description="Type of the question e.g. short_answer, long_answer, use_cases, etc.")


class QuestionTypeRouter(BaseAgent):
    def __init__(self, state, tools, llm, prompt=None):
        self.name = "question_type_router"
        self.prompt = prompt
        super().__init__(state, tools, llm)

    async def arun(self):
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt,
            llm=self.llm,
            placeholder_input={"user_query": self.state['messages'][-1].content},
            validator=QuestionType
        )
        self.state['question_type'] = parsed_response.get('question_type')
        print("Parsed response from question type router:", parsed_response)
        return Command(update={"question_type": parsed_response.get('question_type')},
                       goto=parsed_response.get('question_type'))
