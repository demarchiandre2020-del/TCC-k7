/**
 * wiiiiii.js - Arquivo de controle JavaScript do Almoxarifado
 */

// Função de Login
async function login() {
    const matricula = document.getElementById("matricula").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const tipo = document.querySelector('input[name="tipo"]:checked').value;

    if (!matricula || !email || !password) {
        Swal.fire({
            icon: 'warning',
            title: 'Atenção',
            text: 'Por favor, preencha todos os campos.',
            confirmButtonColor: '#365AEB'
        });
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ matricula, email, password, tipo })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: 'Login realizado com sucesso! Redirecionando...',
                timer: 1500,
                showConfirmButton: false
            });
            setTimeout(() => {
                window.location.href = "/estoque";
            }, 1500);
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: data.error || 'Credenciais inválidas.',
                confirmButtonColor: '#365AEB'
            });
        }
    } catch (error) {
        console.error(error);
        Swal.fire({
            icon: 'error',
            title: 'Erro de Conexão',
            text: 'Não foi possível conectar ao servidor.',
            confirmButtonColor: '#365AEB'
        });
    }
}

// Função de Cadastro
async function cadastrar() {
    const nome = document.getElementById("nome").value.trim();
    const matricula = document.getElementById("matricula").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const password_confirm = document.getElementById("password_confirm").value.trim();
    const permisao = document.getElementById("permisao").value;

    if (!nome || !matricula || !email || !password || !password_confirm) {
        Swal.fire({
            icon: 'warning',
            title: 'Atenção',
            text: 'Todos os campos são obrigatórios.',
            confirmButtonColor: '#365AEB'
        });
        return;
    }

    if (password !== password_confirm) {
        Swal.fire({
            icon: 'error',
            title: 'Senhas Diferentes',
            text: 'A confirmação de senha não coincide!',
            confirmButtonColor: '#365AEB'
        });
        return;
    }

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ nome, matricula, email, password, permisao })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: 'Cadastro de usuário efetuado com sucesso!',
                timer: 2000,
                showConfirmButton: false
            });
            setTimeout(() => {
                window.location.href = "/estoque";
            }, 2000);
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: data.error || 'Erro ao efetuar cadastro.',
                confirmButtonColor: '#365AEB'
            });
        }
    } catch (error) {
        console.error(error);
        Swal.fire({
            icon: 'error',
            title: 'Erro de Conexão',
            text: 'Erro ao tentar se conectar ao servidor.',
            confirmButtonColor: '#365AEB'
        });
    }
}