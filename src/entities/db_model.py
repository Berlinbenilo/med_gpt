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


sqlite_db.connect()
sqlite_db.create_tables([ImageIngestion, FileIngestion, FileIngestionStatus], safe=True)
