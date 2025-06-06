from peewee import *

sqlite_db = SqliteDatabase('database.db')

class BaseModel(Model):
    class Meta:
        database = sqlite_db

class Image(BaseModel):
    image_id = CharField(primary_key=True)
    file_id = CharField()
    file_name = CharField()

class File(BaseModel):
    chunk_id = CharField(primary_key=True)
    file_id = CharField()
    file_name = CharField()


sqlite_db.connect()
sqlite_db.create_tables([Image, File], safe=True)



