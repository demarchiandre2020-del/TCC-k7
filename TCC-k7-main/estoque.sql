CREATE DATABASE IF NOT EXISTS almoxarifado;
USE almoxarifado;

-- Tabela do estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT AUTO_INCREMENT,
    nome VARCHAR(64) NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    estoque_minimo INT NOT NULL DEFAULT 0,
    descricao VARCHAR(255) NULL,
    preco DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    foto VARCHAR(255) NULL,
    categoria VARCHAR(32) NOT NULL, -- elétrica, mecânica, geral
    PRIMARY KEY (id)
);

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    matricula VARCHAR(32) NOT NULL,
    email VARCHAR(48) NOT NULL,
    senha VARCHAR(255) NOT NULL, -- Necessário para hashes bcrypt (60+ caracteres)
    permisao TINYINT(1) NOT NULL DEFAULT 0, -- 1 para admin, 0 para user
    PRIMARY KEY (email)
);

-- Tabela de histórico de movimentações (entrada/saída)
CREATE TABLE IF NOT EXISTS historico (
    id INT AUTO_INCREMENT,
    usuario_email VARCHAR(48) NOT NULL,
    item_id INT NOT NULL,
    quantidade INT NOT NULL,
    tipo VARCHAR(10) NOT NULL, -- 'entrada' ou 'saida'
    finalidade VARCHAR(255) NULL, -- Ex: "Aula do professor Roger"
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (usuario_email) REFERENCES usuarios(email) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES estoque(id) ON DELETE CASCADE
);

-- Inserção de dados iniciais com senhas bcrypt
-- admin123 -> $2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/zBkqquDzV1a55F5.D.i3.Jz1O.
-- user123  -> $2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/zBkqquDz.8vO144G63d.oW63pG
INSERT INTO usuarios (matricula, email, senha, permisao) VALUES 
('ademiro', 'admin@gmail.com', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/zBkqquDzV1a55F5.D.i3.Jz1O.', 1)
ON DUPLICATE KEY UPDATE senha=VALUES(senha);

INSERT INTO usuarios (matricula, email, senha, permisao) VALUES 
('usairo', 'user@gmail.com', '$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/zBkqquDz.8vO144G63d.oW63pG.', 0)
ON DUPLICATE KEY UPDATE senha=VALUES(senha);
