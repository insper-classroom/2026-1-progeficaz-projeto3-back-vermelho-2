from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv('.cred')

client = MongoClient(os.getenv("MONGO_URI"))
db = client["planejador_carreiras"]
collection = db["cursos"]