CREATE DATABASE almoxarifado;
USE almoxarifado;

CREATE TABLE estoque(
	id INT,
	nome VARCHAR(32) NOT NULL,
	quantidade INT,
	categoria VARCHAR(24) NOT NULL,
	descricao VARCHAR(64) NOT NULL,
    PRIMARY KEY (`id`)
	);

CREATE TABLE usuarios (
	email VARCHAR(48) NOT NULL,
    senha VARCHAR(32) NOT NULL,
    permisao BOOL,
    PRIMARY KEY (`email`)
	);

INSERT INTO usuarios (email, senha, permisao) VALUES ('admin@gmail.com', 'admin123', 1)
INSERT INTO usuarios (email, senha, permisao) VALUES ('user@gmail.com', 'user123', 0)
