import pytest
import json
from unittest.mock import MagicMock, patch
import server

MOCK_CURSOS = [
    {
        "_id": "abc123",
        "titulo": "Python",
        "descricao": "Curso completo de Python",
        "local": ["USP - Universidade de São Paulo"]
    },
    {
        "_id": "def456",
        "titulo": "Django",
        "descricao": "Curso de Django com REST API",
        "local": ["USP - Universidade de São Paulo"]
    }
]

@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as client:
        yield client

@patch("utils.col")
def test_get_cursos(mock_col, client):
    mock_col.find.return_value = MOCK_CURSOS
    response = client.get("/cursos")
    assert response.status_code == 200
    assert response.get_json() == MOCK_CURSOS

@patch("utils.col")
def test_get_curso(mock_col, client):
    mock_col.find_one.return_value = MOCK_CURSOS[0]
    response = client.get("/cursos/Python")
    assert response.status_code == 200
    assert response.get_json()["titulo"] == "Python"

@patch("utils.col")
def test_get_curso_404(mock_col, client):
    mock_col.find_one.return_value = None
    response = client.get("/cursos/Nonexisty")
    assert response.status_code == 404
    assert response.get_json()["erro"] == "Curso não encontrado"

@patch("utils.col")
def test_post_curso(mock_col, client):
    novo_curso = {
        "titulo": "Flask",
        "descricao": "Curso completo de Flask",
        "local": ["UFRGS - Universidade Federal do Rio Grande do Sul"]
    }
    mock_col.find_one.return_value = None
    mock_col.insert_one.return_value.inserted_id = "ghi789"
    response = client.post("/cursos", json=novo_curso)
    assert response.status_code == 201
    assert response.get_json()["_id"] is not None

@patch("utils.col")
def test_post_curso_duplicado(mock_col, client):
    curso_duplicado = {
        "titulo": "Python",
        "descricao": "Curso completo de Python",
        "local": ["USP - Universidade de São Paulo"]
    }
    mock_col.find_one.return_value = MOCK_CURSOS[0]
    response = client.post("/cursos", json=curso_duplicado)
    assert response.status_code == 400
    assert response.get_json()["erro"] == "Curso já existe!"

def test_post_curso_dados_incompletos(client):
    curso_incompleto = {"titulo": "Curso"}
    response = client.post("/cursos", json=curso_incompleto)
    assert response.status_code == 400
    assert response.get_json()["erro"] == "Dados incompletos para adicionar o curso"

@patch("utils.col")
def test_put_curso(mock_col, client):
    mock_col.update_one.return_value.modified_count = 1
    curso_atualizado = {"descricao": "Descrição atualizada", "local": ["Presencial"]}
    response = client.put("/cursos/Python", json=curso_atualizado)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Curso atualizado com sucesso!"

@patch("utils.col")
def test_put_curso_nada_atualizado(mock_col, client):
    mock_col.update_one.return_value.modified_count = 0
    response = client.put("/cursos/Python", json={})
    assert response.status_code == 400
    assert response.get_json()["message"] == "Nada foi atualizado"

@patch("utils.col")
def test_delete_curso(mock_col, client):
    mock_col.delete_one.return_value.deleted_count = 1
    response = client.delete("/cursos/Python")
    assert response.status_code == 200
    assert "deletado com sucesso" in response.get_json()["message"]

@patch("utils.col")
def test_delete_curso_nao_encontrado(mock_col, client):
    mock_col.delete_one.return_value.deleted_count = 0
    response = client.delete("/cursos/aaaaa")
    assert response.status_code == 404
    assert response.get_json()["erro"] == "Curso não encontrado"