from flask import Flask, render_template, request
import bcrypt
import mysql.connector

app = Flask(__name__)

def validar_login(user, password):
    banco = mysql.connector.connect(
        host = 'localhost',
        port= 3306,
        user = 'root',
        password = '',
        database = 'almoxarifado'
    )
    cursor = banco.cursor()

    query = "SELECT nome, senha FROM usuarios WHERE nome = %s"
    user = (user,)
    cursor.execute(query, user)
    resultado = cursor.fetchall()

    if resultado is None:
        login_valido = False
        return login_valido

    print(resultado[0][0])
    validacao = bcrypt.checkpw(password.encode('utf-8'), resultado[0][1].encode('utf-8'))
    user = user[0]

    if resultado[0][0] == user and validacao:
        login_valido = True
    else:
        login_valido = False

    return login_valido

@app.route('/login_incorreto.html')
def login_incorreto():
    return render_template('login_incorreto.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/estoque.html', methods=['POST', 'GET'])
def estoque():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')

        login_validado = validar_login(user, password)

        if not login_validado:
            return render_template('login_incorreto.html')

    banco = mysql.connector.connect(
        host = 'localhost',
        port= 3306,
        user = 'root',
        password = '',
        database = 'almoxarifado'
    )

    cursor = banco.cursor()
    query = "SELECT * FROM estoque"
    cursor.execute(query)

    resultado = cursor.fetchall()
    banco.commit()

    return render_template('estoque.html', resultado=resultado)

@app.route('/cadastro.html')
def cadastro():
    return render_template('cadastro.html')

@app.route('/movimentacao.html')
def movimentacao():
    return render_template('movimentacao.html')

@app.route('/movimento_concluido.html', methods=['POST'])
def movimento_concluido():
    nome = request.form.get('nome_item')
    qtde = request.form.get('qtde')
    selecao = request.form.get('selecao')

    banco = mysql.connector.connect(
        host = 'localhost',
        port= 3306,
        user = 'root',
        password = '',
        database = 'almoxarifado'
    )

    cursor = banco.cursor()
    nome = (nome,)
    query = "SELECT qtde FROM estoque WHERE nome = %s;"

    cursor.execute(query, nome)

    qtde_banco = cursor.fetchone()
    qtde_banco = qtde_banco[0]
    qtde_banco = int(qtde_banco)

    print(type(selecao))

    if selecao == '1':
        qtde = int(qtde)
        qtde = qtde_banco + qtde

    if selecao == '2':
        qtde = int(qtde)
        qtde = qtde_banco - qtde

    nome = nome[0]
    query = "UPDATE estoque SET qtde = %s WHERE nome = %s;"

    valores = [qtde, nome]

    cursor.execute(query, valores)
    banco.commit()

    return render_template('movimento_concluido.html')

@app.route('/cadastro_concluido.html', methods=['POST'])
def concluido():

    nome = request.form.get('nome_item')
    descricao = request.form.get('descricao')
    preco = request.form.get('preco')
    qtde = request.form.get('qtde')
    foto = request.form.get('foto')
    categoria = request.form.get('categoria')
    estoque_minimo = request.form.get('estoque_min')

    banco = mysql.connector.connect(
        host = 'localhost',
        port= 3306,
        user = 'root',
        password = '',
        database = 'almoxarifado'
    )

    cursor = banco.cursor()
    
    query = "INSERT INTO estoque(`nome`, `qtde`, `estoque_min`, `descricao`, `preco`, `foto`, `categoria`) VALUES ('" + nome + "'," + qtde + "," + estoque_minimo + ",'" + descricao + "', " + preco + ", '" + foto + "', '" + categoria + "');"
    cursor.execute(query)
    banco.commit()

    print(query)

    return render_template('cadastro_concluido.html')

@app.route('/inserir_users.html')
def inserir_users():
    return render_template('inserir_users.html')

@app.route('/inserir_user_concluido.html', methods=['POST'])
def inserir_user_concluido():

    banco = mysql.connector.connect(
        host = 'localhost',
        port= 3306,
        user = 'root',
        password = '',
        database = 'almoxarifado'
    )

    cursor = banco.cursor()

    user = request.form.get('user')
    senha = request.form.get('senha')
    tipo = request.form.get('selecao')

    bytes_senha = senha.encode('utf-8')
    hash_senha = bcrypt.hashpw(bytes_senha, bcrypt.gensalt())

    query = "INSERT INTO usuarios (nome, senha, permissao) VALUES (%s, %s, %s)"
    valores = (user, hash_senha, tipo)

    cursor.execute(query, valores)
    banco.commit()

    return render_template('inserir_user_concluido.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')