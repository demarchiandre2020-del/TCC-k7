CREATE DATABASE IF NOT EXISTS almoxarifado;
USE almoxarifado;

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    email VARCHAR(100) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    permisao INT DEFAULT 0, -- 0 = Usuário comum, 1 = Administrador
    PRIMARY KEY (email)
);

-- Tabela de Estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    quantidade INT DEFAULT 0,
    categoria VARCHAR(50) NOT NULL,
    descricao VARCHAR(255)
);

-- Tabela de Histórico de Movimentações
CREATE TABLE IF NOT EXISTS historico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_email VARCHAR(100) NOT NULL,
    item_nome VARCHAR(100) NOT NULL,
    quantidade INT NOT NULL, -- Positivo para entrada, Negativo para saída
    tipo VARCHAR(20) NOT NULL, -- 'Entrada' ou 'Saída'
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_email) REFERENCES usuarios (email) ON DELETE CASCADE
);

-- Usuário Administrador Inicial (Senha padrão: admin123)
-- Inserido com hash PBKDF2 correspondente para login seguro
INSERT INTO usuarios (email, nome, senha, permisao) 
VALUES (
    'admin@gmail.com', 
    'Administrador', 
    'scrypt:32768:8:1$pGpxfV1c3Ztqf7fT$4f40f2f01fbeea3336ee3bb66fb2dc41bb925d487299a9a3b6329ef312ccbcf81987d605151528652d8e4f16b2b516b2518be574fe328de3e49e0c51086c8f9c', 
    1
)
ON DUPLICATE KEY UPDATE email=email;
