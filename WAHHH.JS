const mysql = require('mysql2');

// Cria a conexão com o banco de dados
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'sua_senha',
  database: 'seu_banco_de_dados'
});

// Executa a consulta SQL
connection.query(
  'SELECT * FROM usuarios',
  function(err, results, fields) {
    if (err) throw err;
    console.log('Usuários:', results);
  }
);

// Encerra a conexão
connection.end();
