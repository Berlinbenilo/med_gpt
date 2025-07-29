import datetime

from peewee import *

sqlite_db = SqliteDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = sqlite_db


class ImageIngestion(BaseModel):
    image_id = CharField(primary_key=True)
    file_id = CharField()
    file_name = CharField()


class FileIngestion(BaseModel):
    chunk_id = CharField(primary_key=True)
    file_id = CharField()


class FileIngestionStatus(BaseModel):
    file_id = CharField()
    file_name = CharField()
    status = BooleanField()
    file_url = CharField()


class Models(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    model_provider = FloatField()


class ImageSummary(BaseModel):
    image_id = CharField(primary_key=True)
    cropped_image_name = TextField()
    summary = TextField()


# Improved chat session models
class ChatSession(BaseModel):
    """Represents a chat session with metadata"""
    session_id = CharField(primary_key=True)
    user_id = CharField()
    title = CharField(default="New Chat")
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    message_count = IntegerField(default=0)
    model_config = TextField(null=True)  # JSON string of model configuration


class ChatMessage(BaseModel):
    """Represents individual messages in a chat session"""
    message_id = CharField(primary_key=True)
    session_id = CharField()
    role = CharField()  # 'user' or 'assistant'
    content = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    message_order = IntegerField()  # For proper ordering
    node_type = CharField(null=True)  # Which node generated this (for assistant messages)
    metadata = TextField(null=True)  # JSON string for additional metadata

    class Meta:
        indexes = (
            (('session_id', 'message_order'), False),
        )


# Keep the original for backward compatibility, but mark as deprecated
class ConversationHistory(BaseModel):
    """DEPRECATED: Use ChatSession and ChatMessage instead"""
    id = AutoField(primary_key=True)
    user_id = CharField()
    conversation_id = CharField()
    user_query = TextField()
    response = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)


sqlite_db.connect()
sqlite_db.create_tables([ImageIngestion, FileIngestion, FileIngestionStatus, Models, ImageSummary, 
                        ChatSession, ChatMessage, ConversationHistory],
                        safe=True)
