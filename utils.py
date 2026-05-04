from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv('.cred')

client = MongoClient(os.getenv("MONGO_URI"))
db = client["planejador_carreira"]
col = db["cursos"]

def serialize(doc):
    return {
        "_id": str(doc["_id"]),
        "category": doc["category"],
        "value_key": doc["value_key"],
        "response": doc["response"]
    }

def get_all_cursos():
    cursos = list(col.find())
    return [serialize(c) for c in cursos]

def get_one_curso(nome):
    curso = col.find_one({ "titulo": nome })
    if curso:
        return serialize(curso)
    return None

def add_curso(titulo, descricao, local):
    if col.find_one({"titulo": titulo}):
        return None
    
    novo_curso = {
        "titulo": titulo,
        "descricao": descricao,
        "local": local
    }

    result = col.insert_one(novo_curso)
    return str(result.inserted_id)

def update_curso(titulo, descricao=None, local=None):
    updated = {}
    
    if descricao is not None:
        updated["descricao"] = descricao
        
    if local is not None:
        updated["local"] = local
        
    if not updated:
        return 0
    
    return col.update_one(
        {"titulo": titulo},
        {"$set": updated}
    ).modified_count
    
def delete_curso(titulo):
    return col.delete_one({"titulo": titulo}).deleted_count