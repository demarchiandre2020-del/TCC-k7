# os imports necessarios
from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import mysql.connector as mysql
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re

# configuração basica da WEB
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")
app.permanent_session_lifetime = timedelta(hours=24)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# configuração base do DB
def get_db_connection():
    """
    Estabelece uma conexão com o database, se estabelecer ele mostrará o objeto, se falhar vai mostrar uma mensagem de erro
    """
    try:
        connection = mysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "username"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "almoxarifado"),
            autocommit=True,
            connection_timeout=10
        )  
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def validate_email(email):
    """Valida formato de email"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

# ROTAS para paginas
@app.route("/")
def index():
    """
    Index route - shows login page
    """
    if 'email' in session:
        return redirect(url_for("estoque"))
    return render_template("index.html")


@app.route("/cadastrar")
def cadastrar():
    """
    Cadastrar route - registration page
    """
    return render_template("cadastrar.html")

# API endpoint for login
@app.route("/api/login", methods=["POST"])
def login():
    """
    API endpoint for login
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        tipo = data.get("tipo", "usuario").strip()
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if user and check_password_hash(user['senha'], password):
            session['email'] = email
            session['permisao'] = user['permisao']
            session['matricula'] = user['matricula']
            session.permanent = True
            
            # Retorna tipo de usuário
            tipo_usuario = "admin" if user['permisao'] == 1 else "usuario"
            return jsonify({"success": True, "tipo": tipo_usuario}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Server error"}), 500


# API endpoint for user registration
@app.route("/api/register", methods=["POST"])
def register():
    """
    API endpoint for user registration
    """
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        if not all([nome, email, password]):
            return jsonify({"error": "All fields required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor()
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO usuarios (matricula, nome, email, senha, permisao) VALUES (%s, %s, %s, %s, %s)",
                (nome, nome, email, hashed_password, 0)
            )
            cursor.close()
            connection.close()
            return jsonify({"success": True}), 201
        except mysql.connector.errors.IntegrityError:
            cursor.close()
            connection.close()
            return jsonify({"error": "Email already registered"}), 409
            
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({"error": "Server error"}), 500 

# Authentication route
@app.route("/logout")
def logout():
    """
    Logout route - clears session
    """
    session.clear()
    return redirect(url_for("index"))


@app.route("/estoque")
def estoque():
    """
    Estoque route - mostra os dados do inventario
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
            error_msg = "Database falhou na conexão"
        else:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM estoque")
            data = cursor.fetchall()
            cursor.close()
    except Error as e:
        logger.error(f"Estoque - Database error: {e}")
        data = []
        error_msg = "Failed to retrieve inventory data"
    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template("estoque.html", data=data, error=error_msg, email=session.get('email'), permisao=session.get('permisao'))


# API endpoint to add inventory item
@app.route("/api/item", methods=["POST"])
def add_item():
    """
    API endpoint to add inventory item
    """
    if 'email' not in session or not session.get('permisao'):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        categoria = data.get("categoria", "").strip()
        descricao = data.get("descricao", "").strip()
        
        # Validar e converter tipos
        try:
            quantidade = int(data.get("quantidade", 0))
            preco = float(data.get("preco", 0))
        except (ValueError, TypeError):
            return jsonify({"error": "Quantidade e preço devem ser números"}), 400
        
        if not all([nome, quantidade, categoria, preco]):
            return jsonify({"error": "All required fields must be filled"}), 400
        
        if quantidade <= 0 or preco <= 0:
            return jsonify({"error": "Quantidade e preço devem ser positivos"}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO estoque (nome, quantidade, categoria, preco, descricao) VALUES (%s, %s, %s, %s, %s)",
            (nome, quantidade, categoria, preco, descricao)
        )
        cursor.close()
        connection.close()
        return jsonify({"success": True}), 201
        
    except Exception as e:
        logger.error(f"Add item error: {e}")
        return jsonify({"error": "Server error"}), 500

# Route for withdrawal page
@app.route("/retirada")
def retirada():
    """
    Retirada route - withdrawal page
    """
    if 'email' not in session:
        return redirect(url_for("index"))
    return render_template("retirada.html", email=session.get('email'), permisao=session.get('permisao'))

# Route for history page
@app.route("/historico")
def historico():
    """
    Histórico route - history page
    """
    if 'email' not in session:
        return redirect(url_for("index"))
    
    connection = None
    data = []
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM historico")
            data = cursor.fetchall()
            cursor.close()
    except Error as e:
        logger.error(f"Historico - Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
    
    return render_template("historico.html", data=data, email=session.get('email'), usuario=session.get('email'), permisao=session.get('permisao'))

# Admin route
@app.route("/admin")
def admin():
    """
    Admin route - admin panel
    """
    if 'email' not in session or not session.get('permisao'):
        return redirect(url_for("index"))
    return render_template("admin.html", email=session.get('email'))


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000"))
    )
