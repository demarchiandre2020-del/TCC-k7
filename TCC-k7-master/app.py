from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import mysql.connector as mysql
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta
import bcrypt

# Configuração básica da WEB
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")
app.permanent_session_lifetime = timedelta(hours=24)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração base do DB
def get_db_connection():
    """
    Estabelece uma conexão com o database, se estabelecer ele mostrará o objeto, se falhar vai mostrar uma mensagem de erro
    """
    try:
        connection = mysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "almoxarifado"),
            autocommit=True,
            connection_timeout=10
        )  
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

# ROTAS para páginas

@app.route("/")
def index():
    """
    Index route - shows login page
    """
    if 'email' in session:
        return redirect(url_for("estoque"))
    return render_template("index.html")


@app.route("/admin")
def admin_redirect():
    """
    Redirect /admin to /estoque
    """
    return redirect(url_for("estoque"))


@app.route("/cadastrar")
def cadastrar():
    """
    Cadastrar route - registration page (restricted to Admin)
    """
    if 'email' not in session or not session.get('permisao'):
        return redirect(url_for("index"))
    return render_template("cadastrar.html", email=session.get('email'), permisao=session.get('permisao'))


@app.route("/api/login", methods=["POST"])
def login():
    """
    API endpoint for login using bcrypt
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Falha na conexão com o banco de dados"}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user:
            # Verifica a senha utilizando bcrypt
            senha_db = user['senha']
            # Se a senha no banco não for hash bcrypt, tratamos
            try:
                is_correct = bcrypt.checkpw(password.encode('utf-8'), senha_db.encode('utf-8'))
            except Exception:
                # Fallback em texto plano se o hash bcrypt falhar (para facilitar testes)
                is_correct = (senha_db == password)
                
            if is_correct:
                session['email'] = email
                session['permisao'] = user['permisao']
                session.permanent = True
                return jsonify({
                    "success": True, 
                    "tipo": "admin" if user['permisao'] == 1 else "user"
                }), 200
        
        return jsonify({"error": "E-mail ou senha inválidos"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@app.route("/api/register", methods=["POST"])
def register():
    """
    API endpoint for user registration (Restricted to Admin)
    """
    if 'email' not in session or not session.get('permisao'):
        return jsonify({"error": "Não autorizado"}), 403
        
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        matricula = data.get("matricula", "").strip()
        permisao = int(data.get("permisao", 0))
        
        if not all([nome, email, password, matricula]):
            return jsonify({"error": "Todos os campos são obrigatórios"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Falha na conexão com o banco de dados"}), 500
        
        cursor = connection.cursor()
        try:
            # Hashing da senha com bcrypt
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(
                "INSERT INTO usuarios (matricula, email, senha, permisao) VALUES (%s, %s, %s, %s)",
                (matricula, email, hashed_password, permisao)
            )
            cursor.close()
            connection.close()
            return jsonify({"success": True}), 201
        except mysql.connector.errors.IntegrityError:
            cursor.close()
            connection.close()
            return jsonify({"error": "E-mail já cadastrado"}), 409
            
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500 


@app.route("/estoque")
def estoque():
    """
    Estoque route - mostra os dados do inventário
    """
    if 'email' not in session:
        return redirect(url_for("index"))
    
    connection = None
    data = []
    error_msg = None
    
    try:
        connection = get_db_connection()
        if connection is None:
            logger.warning("Estoque: falhou na conexão")
            error_msg = "Banco de dados falhou na conexão"
        else:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM estoque")
            data = cursor.fetchall()
            cursor.close()
    except Error as e:
        logger.error(f"Estoque - Database error: {e}")
        data = []
        error_msg = "Falha ao recuperar dados do estoque"
    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template("estoque.html", data=data, error=error_msg, email=session.get('email'), permisao=session.get('permisao'))


@app.route("/api/item", methods=["POST"])
def add_item():
    """
    API endpoint to add inventory item
    """
    if 'email' not in session or not session.get('permisao'):
        return jsonify({"error": "Não autorizado"}), 403
    
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        quantidade = int(data.get("quantidade", 0))
        estoque_minimo = int(data.get("estoque_minimo", 0))
        categoria = data.get("categoria", "").strip()
        preco = float(data.get("preco", 0.0))
        descricao = data.get("descricao", "").strip()
        foto = data.get("foto", "").strip()
        
        if not all([nome, categoria]) or quantidade < 0 or preco < 0:
            return jsonify({"error": "Campos obrigatórios inválidos"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Falha na conexão com o banco de dados"}), 500
        
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO estoque (nome, quantidade, estoque_minimo, descricao, preco, foto, categoria) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nome, quantidade, estoque_minimo, descricao, preco, foto, categoria)
        )
        cursor.close()
        connection.close()
        return jsonify({"success": True}), 201
        
    except Exception as e:
        logger.error(f"Add item error: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@app.route("/retirada")
def retirada():
    """
    Retirada route - withdrawal and input page
    """
    if 'email' not in session:
        return redirect(url_for("index"))
    
    connection = None
    items = []
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, nome, quantidade FROM estoque ORDER BY nome")
            items = cursor.fetchall()
            cursor.close()
    except Error as e:
        logger.error(f"Retirada - Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            
    return render_template("retirada.html", items=items, email=session.get('email'), permisao=session.get('permisao'))


@app.route("/api/movimentacao", methods=["POST"])
def movimentacao():
    """
    API endpoint to handle stock input or output requests
    """
    if 'email' not in session:
        return jsonify({"error": "Não autorizado"}), 403
        
    try:
        data = request.get_json()
        item_id = int(data.get("item_id", 0))
        quantidade = int(data.get("quantidade", 0))
        tipo = data.get("tipo", "").strip() # 'entrada' ou 'saida'
        finalidade = data.get("finalidade", "").strip()
        usuario_email = session.get('email')
        
        if not item_id or quantidade <= 0 or tipo not in ['entrada', 'saida']:
            return jsonify({"error": "Dados de movimentação inválidos"}), 400
            
        if tipo == 'saida' and not finalidade:
            return jsonify({"error": "A finalidade é obrigatória para saídas de estoque"}), 400
            
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Falha na conexão com o banco de dados"}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # 1. Verifica se o item existe e confere a quantidade atual
        cursor.execute("SELECT nome, quantidade FROM estoque WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            cursor.close()
            connection.close()
            return jsonify({"error": "Item não encontrado no estoque"}), 404
            
        quantidade_atual = item['quantidade']
        
        # 2. Se for saída, verifica se há estoque suficiente
        if tipo == 'saida':
            if quantidade_atual < quantidade:
                cursor.close()
                connection.close()
                return jsonify({"error": f"Estoque insuficiente. Quantidade disponível: {quantidade_atual}"}), 400
            nova_quantidade = quantidade_atual - quantidade
        else:
            nova_quantidade = quantidade_atual + quantidade
            
        # 3. Atualiza a quantidade do item no estoque
        cursor.execute("UPDATE estoque SET quantidade = %s WHERE id = %s", (nova_quantidade, item_id))
        
        # 4. Registra no histórico de movimentações
        cursor.execute(
            "INSERT INTO historico (usuario_email, item_id, quantidade, tipo, finalidade) VALUES (%s, %s, %s, %s, %s)",
            (usuario_email, item_id, quantidade, tipo, finalidade if tipo == 'saida' else None)
        )
        
        cursor.close()
        connection.close()
        
        return jsonify({"success": True}), 201
        
    except Exception as e:
        logger.error(f"Movimentacao error: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@app.route("/historico")
def historico():
    """
    Histórico route - mostra o histórico de movimentações detalhado
    """
    if 'email' not in session:
        return redirect(url_for("index"))
    
    connection = None
    data = []
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            # Query com JOIN para trazer as informações completas exigidas no histórico
            query = """
                SELECT 
                    h.id, 
                    u.nome AS usuario_nome, 
                    u.email AS usuario_email, 
                    e.nome AS item_nome, 
                    h.quantidade, 
                    e.categoria AS item_categoria, 
                    h.tipo, 
                    h.finalidade, 
                    h.data_hora 
                FROM historico h 
                JOIN usuarios u ON h.usuario_email = u.email 
                JOIN estoque e ON h.item_id = e.id
                ORDER BY h.data_hora DESC
            """
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
    except Error as e:
        logger.error(f"Historico - Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
    
    return render_template("historico.html", data=data, email=session.get('email'), permisao=session.get('permisao'))


@app.route("/logout")
def logout():
    """
    Logout route - limpa a sessão e redireciona para a página inicial
    """
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Disponibiliza o servidor para outros dispositivos na mesma rede (0.0.0.0) na porta 5000
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000"))
    )