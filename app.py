from flask import Flask, render_template
import mysql.connector as mysql

app = Flask(__name__)

db = mysql.connect(
    host="localhost",
    user="username",
    password="password",
    database="name"
)


def get_db_connection():
    return mysql.connect(**db_config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM table_name")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', items=data)

@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/estoque')
def estoque():
    return render_template('estoque.html')

if __name__ == '__main__':
    app.run(debug=True)  



