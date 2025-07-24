import datetime

from langgraph.types import Command
from pydantic import BaseModel, Field

from backend.src.agents.base import BaseAgent
from backend.src.entities.db_model import ConversationHistory


class QuestionRephraser(BaseModel):
    rephrased_query: str = Field(..., description="Rephrase the question based on the previous conversation question")


class QueryPreprocessor(BaseAgent):
    def __init__(self, state, tools, llm, prompt=None, session_id=None):
        self.name = "query_preprocessor"
        self.prompt = prompt
        self.session_id = session_id
        super().__init__(state, tools, llm)

    async def arun(self):
        previous_conversation_text = ConversationHistory.select(ConversationHistory.user_query).where(
            ConversationHistory.conversation_id == self.session_id).order_by(
            ConversationHistory.timestamp.desc()).limit(7)
        previous_conversations = "\n".join([row.user_query for row in previous_conversation_text])
        parsed_response = self.parser_obj.invoke_with_parser(
            prompt_template=self.prompt,
            llm=self.llm,
            placeholder_input={"user_query": self.state['messages'][-1].content,
                               "previous_conversation_context": previous_conversations},
            validator=QuestionRephraser
        )
        self.state['question_type'] = parsed_response.get('question_type')
        print("rephrased query:", parsed_response)
        ConversationHistory.insert({
            'conversation_id': self.session_id,
            'user_query': parsed_response.get('rephrased_query'),
            'response': "",
            'timestamp': datetime.datetime.now()
        }).execute()
        return Command(update={"messages": [parsed_response.get('rephrased_query')]},
                       goto="question_type_router", )
