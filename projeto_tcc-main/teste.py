import bcrypt

tentativa_login = "letici"

senha_banco = "$2b$12$eeDA9dp1o95ukR/C8kfsU.mnuv147ybOqyzCoABgW//lj3Q9I5zGe"

# Comparando a senha digitada com o hash armazenado
if bcrypt.checkpw(tentativa_login.encode('utf-8'), senha_banco.encode('utf-8')):
    print("Sucesso: A senha está correta!")
else:
    print("Erro: Senha incorreta.")