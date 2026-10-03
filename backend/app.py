from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import conectar_banco
from models import Usuario
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def carregar_usuario(user_id):

    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, nome, email, perfil FROM usuarios WHERE id = %s",
            (user_id,)
        )

        dados = cursor.fetchone()

        if dados:
            return Usuario(
                dados["id"],
                dados["nome"],
                dados["email"],
                dados["perfil"]
            )

        return None

    finally:
        cursor.close()
        conexao.close()


@app.route("/")
def inicio():
    if current_user.is_authenticated:
        return redirect(url_for("painel"))

    return redirect(url_for("login"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip()
        senha = request.form.get("senha", "")
        perfil = request.form.get("perfil", "")

        if not nome or not email or not senha or not perfil:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for("cadastro"))

        if len(senha) < 8:
            flash("A senha deve possuir pelo menos 8 caracteres.", "danger")
            return redirect(url_for("cadastro"))

        if perfil not in ["CLIENTE", "PRESTADOR"]:
            flash("Perfil inválido.", "danger")
            return redirect(url_for("cadastro"))

        senha_hash = generate_password_hash(senha)

        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT id FROM usuarios WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("Este e-mail já está cadastrado.", "warning")
                return redirect(url_for("cadastro"))

            comando = """
                INSERT INTO usuarios
                (nome, email, senha, telefone, perfil)
                VALUES (%s, %s, %s, %s, %s)
            """

            valores = (nome, email, senha_hash, telefone, perfil)

            cursor.execute(comando, valores)
            conexao.commit()

            flash("Cadastro realizado com sucesso! Faça seu login.", "success")
            return redirect(url_for("login"))

        except Exception as erro:
            if conexao:
                conexao.rollback()

            print("Erro ao cadastrar usuário:", erro)
            flash("Ocorreu um erro ao realizar o cadastro.", "danger")

        finally:
            if cursor:
                cursor.close()

            if conexao and conexao.is_connected():
                conexao.close()

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("painel"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, nome, email, senha, perfil
                FROM usuarios
                WHERE email = %s
                """,
                (email,)
            )

            dados = cursor.fetchone()

            if dados and check_password_hash(dados["senha"], senha):

                usuario = Usuario(
                    dados["id"],
                    dados["nome"],
                    dados["email"],
                    dados["perfil"]
                )

                login_user(usuario)

                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("painel"))

            flash("E-mail ou senha incorretos.", "danger")

        except Exception as erro:
            print("Erro no login:", erro)
            flash("Não foi possível realizar o login.", "danger")

        finally:
            if cursor:
                cursor.close()

            if conexao and conexao.is_connected():
                conexao.close()

    return render_template("login.html")


@app.route("/painel")
@login_required
def painel():
    return render_template("painel.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash("Você saiu da sua conta.", "success")

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)