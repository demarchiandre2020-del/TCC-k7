const usuario = document.getElementById("usuario");
const admin = document.getElementById("admin");
const cadastrarBtn = document.getElementById("cadastrar");

// Botão cadastrar inicia bloqueado
cadastrarBtn.disabled = true;

// Habilita cadastro apenas para admin
admin.addEventListener("change", () => {
    cadastrarBtn.disabled = false;
});

usuario.addEventListener("change", () => {
    cadastrarBtn.disabled = true;
});

// Função de cadastro
function cadastrar() {
    window.location.href = "/cadastro";
}

// Função de login
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const tipo = document.querySelector('input[name="tipo"]:checked').id;

    if (!email || !password) {
        alert("Preencha todos os campos.");
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password,
                tipo
            })
        });

        const data = await response.json();

        if (data.success) {

            if (data.tipo === "admin") {
                window.location.href = "/admin";
            } else {
                window.location.href = "/estoque";
            }

        } else {
            alert(data.error || "Login inválido.");
        }

    } catch (error) {
        console.error(error);
        alert("Erro ao conectar com o servidor.");
    }
}