from flask import Flask, render_template_string, request, jsonify
import utils

app = Flask(__name__)

@app.route('/')
def pagina_inicial():
    return render_template_string('''
        <p>Servidor rodando...</p>
        <p>Acesse /cursos para acessar a API.</p>
    ''')

@app.route("/cursos", methods=["GET"])
def get_cursos():
    cursos = utils.get_all_cursos()
    return jsonify(cursos)

@app.route("/cursos/<titulo>", methods=["GET"])
def get_curso(titulo):
    curso = utils.get_one_curso(titulo)
    
    if curso:
        return jsonify(curso), 200
    
    return jsonify({"erro": "Curso não encontrado"}), 404

@app.route("/cursos", methods=["POST"])
def novo_curso():
    data = request.json
    
    titulo = data.get("titulo")
    descricao = data.get("descricao")
    local = data.get("local")
    
    if not titulo or not descricao or not isinstance(local, list):
        return jsonify({"erro": "Dados incompletos para adicionar o curso"}), 400
    
    new_curso = utils.add_curso(titulo, descricao, local)
    
    if new_curso is None:
        return jsonify({"erro": "Curso já existe!"}), 400
    
    return jsonify({"_id": new_curso}), 201

@app.route("/cursos/<titulo>", methods=["PUT"])
def update_curso(titulo):
    data = request.json
    
    descricao = data.get("descricao")
    local = data.get("local")

    updated = utils.update_curso(titulo, descricao, local)
    
    if updated == 0:
        return jsonify({"message": "Nada foi atualizado"}), 400
    
    return jsonify({"message": "Curso atualizado com sucesso!"}), 200

@app.route("/cursos/<titulo>", methods=["DELETE"])
def deletar_curso(titulo):
    deleted = utils.delete_curso(titulo)

    if deleted == 0:
        return jsonify({"erro": "Curso não encontrado"}), 404

    return jsonify({"message": f"Curso '{titulo}' deletado com sucesso"}), 200

if __name__ == "__main__":
    app.run(debug=True)