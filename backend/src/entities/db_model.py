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
    file_id = CharField()
    full_page_name = CharField()
    cropped_image_name = CharField(primary_key=True)
    summary = TextField()
    file_name = CharField()

sqlite_db.connect()
sqlite_db.create_tables([ImageIngestion, FileIngestion, FileIngestionStatus, Models, ImageSummary], safe=True)
