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


class ConversationHistory(BaseModel):
    user_id = CharField()
    conversation_id = CharField()
    user_query = TextField()
    response = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now())


sqlite_db.connect()
sqlite_db.create_tables([ImageIngestion, FileIngestion, FileIngestionStatus, Models, ImageSummary, ConversationHistory],
                        safe=True)
