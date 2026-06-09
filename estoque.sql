CREATE DATABASE almoxarifado;
USE almoxarifado;

CREATE TABLE estoque(
	id INT AUTO_INCREMENT,
	nome VARCHAR(32) NOT NULL,
	quantidade INT NOT NULL,
	categoria VARCHAR(24) NOT NULL,
	preco DECIMAL(10, 2) NOT NULL,
	descricao VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
);

CREATE TABLE usuarios (
	matricula VARCHAR(32) NOT NULL,
	nome VARCHAR(100) NOT NULL,
	email VARCHAR(48) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    permisao TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`email`)
);

CREATE TABLE historico(
	id INT AUTO_INCREMENT,
	usuario_email VARCHAR(48) NOT NULL,
	tipo_movimentacao VARCHAR(20),
	item_nome VARCHAR(32),
	quantidade INT,
	descricao VARCHAR(255),
	data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (`id`),
	FOREIGN KEY (`usuario_email`) REFERENCES usuarios(`email`)
);

-- Inserir usuários de teste (senhas com hash bcrypt - gerar com werkzeug)
-- Senha admin123 com hash
INSERT INTO usuarios (matricula, nome, email, senha, permisao) 
VALUES ('ademiro', 'Ademiro Admin', 'admin@gmail.com', 'pbkdf2:sha256:600000$...[gerar hash]...', 1);

-- Senha user123 com hash
INSERT INTO usuarios (matricula, nome, email, senha, permisao) 
VALUES ('usairo', 'Usuário Teste', 'user@gmail.com', 'pbkdf2:sha256:600000$...[gerar hash]...', 0);
