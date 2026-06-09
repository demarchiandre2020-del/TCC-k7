from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import mysql.connector as mysql
from mysql.connector import Error
import sqlite3
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar aplicação Flask
app = Flask(__name__, template_folder='template')
app.secret_key = os.getenv("SECRET_KEY", "dev-key-senai-tcc-warehouse-2026")
app.permanent_session_lifetime = timedelta(hours=24)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gerenciador de Banco de Dados para suportar MySQL e SQLite como fallback automático
class DBManager:
    def __init__(self):
        self.use_sqlite = False
        # Tenta conectar ao MySQL de acordo com o .env
        try:
            connection = mysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "username"),
                password=os.getenv("DB_PASSWORD", "password"),
                database=os.getenv("DB_NAME", "almoxarifado"),
                connection_timeout=2
            )
            connection.close()
            logger.info("Conectado ao MySQL com sucesso.")
        except Exception as e:
            logger.warning(f"Conexão com MySQL falhou: {e}. Usando SQLite local como fallback.")
            self.use_sqlite = True
            self.init_sqlite()

    def init_sqlite(self):
        """Inicializa as tabelas no SQLite local se não existirem."""
        conn = sqlite3.connect("almoxarifado.db")
        cursor = conn.cursor()
        
        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                email VARCHAR(100) NOT NULL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                senha VARCHAR(255) NOT NULL,
                permisao INT DEFAULT 0
            )
        """)
        
        # Tabela de Estoque
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                quantidade INT DEFAULT 0,
                categoria VARCHAR(50) NOT NULL,
                descricao VARCHAR(255),
                imagem VARCHAR(255) DEFAULT NULL
            )
        """)
        
        # Migração caso a coluna imagem não exista em bancos SQLite existentes
        try:
            cursor.execute("PRAGMA table_info(estoque)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'imagem' not in columns:
                cursor.execute("ALTER TABLE estoque ADD COLUMN imagem VARCHAR(255) DEFAULT NULL")
                logger.info("Coluna 'imagem' adicionada à tabela 'estoque' (SQLite).")
        except Exception as e:
            logger.error(f"Erro ao verificar/migrar coluna imagem no SQLite: {e}")
            
        # Tabela de Histórico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_email VARCHAR(100) NOT NULL,
                item_nome VARCHAR(100) NOT NULL,
                quantidade INT NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_email) REFERENCES usuarios (email)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Banco de dados SQLite inicializado.")

    def get_connection(self):
        """Retorna uma nova conexão de banco de dados ativa."""
        if self.use_sqlite:
            conn = sqlite3.connect("almoxarifado.db")
            conn.row_factory = sqlite3.Row
            return conn
        else:
            return mysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "username"),
                password=os.getenv("DB_PASSWORD", "password"),
                database=os.getenv("DB_NAME", "almoxarifado"),
                autocommit=True
            )

# Instância única do gerenciador de banco de dados
db_mgr = None

def get_db_manager():
    global db_mgr
    if db_mgr is None:
        db_mgr = DBManager()
    return db_mgr

def query_db(query, args=(), commit=False):
    """Executa uma query no banco de dados ativo (MySQL ou SQLite), mapeando os placeholders."""
    mgr = get_db_manager()
    conn = mgr.get_connection()
    try:
        if mgr.use_sqlite:
            # Converte placeholders do padrão MySQL (%s) para o padrão SQLite (?)
            sqlite_query = query.replace("%s", "?")
            cursor = conn.cursor()
            cursor.execute(sqlite_query, args)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
            rv = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rv] if rv else []
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, args)
            if commit:
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
            rv = cursor.fetchall()
            cursor.close()
            return rv
    except Exception as e:
        logger.error(f"Erro na execução da query: {query}. Erro: {e}")
        if mgr.use_sqlite and commit:
            conn.rollback()
        raise e
    finally:
        conn.close()

def seed_database():
    """Semeia o banco com o usuário administrador padrão se não existir e realiza migrações no MySQL se necessário."""
    try:
        # Migração da coluna imagem para o MySQL
        mgr = get_db_manager()
        if not mgr.use_sqlite:
            conn = mgr.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SHOW COLUMNS FROM estoque LIKE 'imagem'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE estoque ADD COLUMN imagem VARCHAR(255) DEFAULT NULL")
                    logger.info("Coluna 'imagem' adicionada à tabela 'estoque' (MySQL).")
            except Exception as ex:
                logger.error(f"Erro ao alterar tabela estoque no MySQL: {ex}")
            finally:
                cursor.close()
                conn.close()

        # Verifica se o admin existe
        admin = query_db("SELECT * FROM usuarios WHERE email = %s", ('admin@gmail.com',))
        if not admin:
            hashed_pwd = generate_password_hash("admin123")
            query_db(
                "INSERT INTO usuarios (email, nome, senha, permisao) VALUES (%s, %s, %s, %s)",
                ('admin@gmail.com', 'Administrador', hashed_pwd, 1),
                commit=True
            )
            logger.info("Usuário Admin ('admin@gmail.com') semeado no banco de dados com a senha padrão 'admin123'.")
    except Exception as e:
        logger.error(f"Falha ao semear o banco de dados: {e}")


# --- ROTAS WEB DE TEMPLATES ---

@app.route("/")
def index():
    """Rota inicial - Página de Login."""
    if 'email' in session:
        return redirect(url_for("estoque"))
    return render_template("index.html")


@app.route("/cadastrar")
def cadastrar():
    """Rota para a página de cadastro de usuários."""
    if 'email' in session:
        return redirect(url_for("estoque"))
    return render_template("cadastrar.html")


@app.route("/estoque")
def estoque():
    """Rota do Painel de Controle do Estoque."""
    if 'email' not in session:
        return redirect(url_for("index"))
    
    data = []
    error_msg = None
    try:
        data = query_db("SELECT * FROM estoque ORDER BY nome ASC")
    except Exception as e:
        logger.error(f"Erro ao recuperar dados de estoque: {e}")
        error_msg = "Não foi possível carregar os itens do estoque."
        
    return render_template(
        "estoque.html", 
        data=data, 
        error=error_msg, 
        email=session.get('email'),
        nome=session.get('nome', 'Usuário'),
        permisao=session.get('permisao', 0)
    )


@app.route("/logout")
def logout():
    """Rota para realizar o logout e limpar a sessão."""
    session.clear()
    return redirect(url_for("index"))


# --- ROTAS DE API (JSON) ---

@app.route("/api/login", methods=["POST"])
def login():
    """Endpoint de Login da API."""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"error": "Preencha todos os campos obrigatórios."}), 400
        
        users = query_db("SELECT * FROM usuarios WHERE email = %s", (email,))
        if not users:
            return jsonify({"error": "E-mail ou senha inválidos."}), 401
        
        user = users[0]
        if check_password_hash(user['senha'], password):
            session['email'] = email
            session['nome'] = user['nome']
            session['permisao'] = user['permisao']
            session.permanent = True
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "E-mail ou senha inválidos."}), 401
            
    except Exception as e:
        logger.error(f"Erro no login API: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor."}), 500


@app.route("/api/register", methods=["POST"])
def register():
    """Endpoint de Registro de Usuários da API."""
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()
        
        if not all([nome, email, password]):
            return jsonify({"error": "Preencha todos os campos."}), 400
            
        if len(password) < 6:
            return jsonify({"error": "A senha deve conter pelo menos 6 caracteres."}), 400
        
        # Verifica se o email já está em uso
        users = query_db("SELECT * FROM usuarios WHERE email = %s", (email,))
        if users:
            return jsonify({"error": "Este endereço de e-mail já está cadastrado."}), 409
            
        hashed_password = generate_password_hash(password)
        query_db(
            "INSERT INTO usuarios (email, nome, senha, permisao) VALUES (%s, %s, %s, %s)",
            (email, nome, hashed_password, 0), # 0 = Usuário comum padrão
            commit=True
        )
        return jsonify({"success": True}), 201
        
    except Exception as e:
        logger.error(f"Erro no cadastro de usuário: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor."}), 500


@app.route("/api/estoque", methods=["GET"])
def get_estoque():
    """Recupera todos os itens do estoque em formato JSON."""
    if 'email' not in session:
        return jsonify({"error": "Não autorizado"}), 401
    try:
        items = query_db("SELECT * FROM estoque ORDER BY nome ASC")
        return jsonify(items), 200
    except Exception as e:
        logger.error(f"Erro ao buscar estoque da API: {e}")
        return jsonify({"error": "Erro ao buscar dados."}), 500


@app.route("/api/item", methods=["POST"])
def add_item():
    """Adiciona um novo item ao estoque (Requer privilégios de Admin)."""
    if 'email' not in session or not session.get('permisao'):
        return jsonify({"error": "Acesso negado. Apenas administradores podem gerenciar estoque."}), 403
    
    try:
        # Usa request.form e request.files para dar suporte a FormData (upload de imagens)
        nome = request.form.get("nome", "").strip()
        quantidade = int(request.form.get("quantidade", 0))
        categoria = request.form.get("categoria", "").strip()
        descricao = request.form.get("descricao", "").strip()
        
        if not nome or not categoria or quantidade < 0:
            return jsonify({"error": "Nome, categoria e quantidade válida são obrigatórios."}), 400
        
        # Upload de Imagem
        image_filename = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '':
                import uuid
                ext = file.filename.split('.')[-1].lower()
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                    image_filename = f"{uuid.uuid4().hex}.{ext}"
                    upload_path = os.path.join(app.root_path, 'static', 'uploads')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, image_filename))
                    image_filename = f"uploads/{image_filename}"
        
        # Insere no banco
        item_id = query_db(
            "INSERT INTO estoque (nome, quantidade, categoria, descricao, imagem) VALUES (%s, %s, %s, %s, %s)",
            (nome, quantidade, categoria, descricao, image_filename),
            commit=True
        )
        
        # Loga no histórico a entrada
        query_db(
            "INSERT INTO historico (usuario_email, item_nome, quantidade, tipo) VALUES (%s, %s, %s, %s)",
            (session['email'], nome, quantidade, 'Entrada'),
            commit=True
        )
        
        return jsonify({"success": True, "id": item_id}), 201
        
    except Exception as e:
        logger.error(f"Erro ao adicionar item: {e}")
        return jsonify({"error": "Erro no servidor ao processar o item."}), 500


@app.route("/api/item/<int:item_id>", methods=["POST", "PUT", "DELETE"])
def manage_item(item_id):
    """Atualiza ou deleta um item do estoque (Requer privilégios de Admin)."""
    if 'email' not in session or not session.get('permisao'):
        return jsonify({"error": "Acesso negado. Apenas administradores podem gerenciar estoque."}), 403
        
    try:
        # Verifica se o item existe
        items = query_db("SELECT * FROM estoque WHERE id = %s", (item_id,))
        if not items:
            return jsonify({"error": "Item não encontrado."}), 404
        item = items[0]
        
        if request.method in ["POST", "PUT"]:
            nome = request.form.get("nome", "").strip()
            quantidade = int(request.form.get("quantidade", 0))
            categoria = request.form.get("categoria", "").strip()
            descricao = request.form.get("descricao", "").strip()
            
            if not nome or not categoria or quantidade < 0:
                return jsonify({"error": "Preencha todos os campos obrigatórios."}), 400
                
            qty_diff = quantidade - item['quantidade']
            image_filename = item['imagem'] # Mantém imagem antiga se não enviar nova
            
            # Se for enviada nova imagem
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and file.filename != '':
                    import uuid
                    ext = file.filename.split('.')[-1].lower()
                    if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                        # Exclui imagem antiga do disco
                        if item['imagem']:
                            old_path = os.path.join(app.root_path, 'static', item['imagem'])
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except Exception as img_err:
                                    logger.error(f"Erro ao remover imagem antiga: {img_err}")
                        
                        # Salva nova imagem
                        new_name = f"{uuid.uuid4().hex}.{ext}"
                        upload_path = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_path, exist_ok=True)
                        file.save(os.path.join(upload_path, new_name))
                        image_filename = f"uploads/{new_name}"
            
            # Atualiza
            query_db(
                "UPDATE estoque SET nome = %s, quantidade = %s, categoria = %s, descricao = %s, imagem = %s WHERE id = %s",
                (nome, quantidade, categoria, descricao, image_filename, item_id),
                commit=True
            )
            
            # Loga mudança na quantidade se houver
            if qty_diff != 0:
                tipo = 'Entrada' if qty_diff > 0 else 'Saída'
                query_db(
                    "INSERT INTO historico (usuario_email, item_nome, quantidade, tipo) VALUES (%s, %s, %s, %s)",
                    (session['email'], nome, qty_diff, tipo),
                    commit=True
                )
            return jsonify({"success": True}), 200
            
        elif request.method == "DELETE":
            # Remove a imagem do disco
            if item['imagem']:
                old_path = os.path.join(app.root_path, 'static', item['imagem'])
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as img_err:
                        logger.error(f"Erro ao remover imagem na exclusão: {img_err}")

            # Remove o item do estoque
            query_db("DELETE FROM estoque WHERE id = %s", (item_id,), commit=True)
            
            # Registra saída de todo o estoque restante
            query_db(
                "INSERT INTO historico (usuario_email, item_nome, quantidade, tipo) VALUES (%s, %s, %s, %s)",
                (session['email'], item['nome'], -item['quantidade'], 'Saída (Exclusão)'),
                commit=True
            )
            return jsonify({"success": True}), 200
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar item {item_id}: {e}")
        return jsonify({"error": "Erro no servidor."}), 500


@app.route("/api/retirada", methods=["POST"])
def perform_retirada():
    """Realiza a retirada de um item do estoque por um usuário logado."""
    if 'email' not in session:
        return jsonify({"error": "Acesso não autorizado."}), 401
        
    try:
        data = request.get_json()
        item_id = data.get("item_id")
        quantidade_retirada = int(data.get("quantidade", 0))
        
        if not item_id or quantidade_retirada <= 0:
            return jsonify({"error": "Selecione um item e insira uma quantidade válida."}), 400
            
        items = query_db("SELECT * FROM estoque WHERE id = %s", (item_id,))
        if not items:
            return jsonify({"error": "Item não encontrado no estoque."}), 404
        item = items[0]
        
        current_qty = item['quantidade']
        if quantidade_retirada > current_qty:
            return jsonify({"error": f"A quantidade solicitada ({quantidade_retirada}) excede o disponível em estoque ({current_qty})."}), 400
            
        # Atualiza quantidade no estoque
        new_qty = current_qty - quantidade_retirada
        query_db("UPDATE estoque SET quantidade = %s WHERE id = %s", (new_qty, item_id), commit=True)
        
        # Grava no histórico a movimentação
        query_db(
            "INSERT INTO historico (usuario_email, item_nome, quantidade, tipo) VALUES (%s, %s, %s, %s)",
            (session['email'], item['nome'], -quantidade_retirada, 'Saída'),
            commit=True
        )
        
        return jsonify({"success": True, "new_quantity": new_qty}), 200
        
    except Exception as e:
        logger.error(f"Erro na retirada de item: {e}")
        return jsonify({"error": "Erro no servidor ao registrar retirada."}), 500


@app.route("/api/historico", methods=["GET"])
def get_historico():
    """Recupera o histórico completo de movimentações."""
    if 'email' not in session:
        return jsonify({"error": "Acesso não autorizado."}), 401
    try:
        historico = query_db("SELECT * FROM historico ORDER BY data_hora DESC")
        return jsonify(historico), 200
    except Exception as e:
        logger.error(f"Erro ao buscar histórico da API: {e}")
        return jsonify({"error": "Erro ao buscar histórico de movimentações."}), 500


if __name__ == "__main__":
    # Inicializa o banco de dados e adiciona admin padrão se necessário
    seed_database()
    
    # Roda a aplicação Flask
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000"))
    )
