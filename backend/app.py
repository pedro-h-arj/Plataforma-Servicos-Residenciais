from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import conectar_banco
from models import Usuario
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def perfil_requerido(perfil):
    def decorator(funcao):
        @wraps(funcao)
        @login_required
        def funcao_protegida(*args, **kwargs):
            if current_user.perfil != perfil:
                flash("Você não possui permissão para acessar esta área.", "danger")
                return redirect(url_for("painel"))

            return funcao(*args, **kwargs)

        return funcao_protegida

    return decorator


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


@app.route("/servicos/cadastrar", methods=["GET", "POST"])
@perfil_requerido("PRESTADOR")
def cadastrar_servico():

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()
        descricao = request.form.get("descricao", "").strip()
        valor_estimado = request.form.get("valor_estimado", "").strip()

        if not nome or not categoria or not descricao:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for("cadastrar_servico"))

        if valor_estimado == "":
            valor = None
        else:
            try:
                valor = float(valor_estimado)

                if valor < 0:
                    flash("O valor não pode ser negativo.", "danger")
                    return redirect(url_for("cadastrar_servico"))

            except ValueError:
                flash("Informe um valor válido.", "danger")
                return redirect(url_for("cadastrar_servico"))

        conexao = None
        cursor = None

        try:
            conexao = conectar_banco()
            cursor = conexao.cursor()

            comando = """
                INSERT INTO servicos
                (prestador_id, nome, categoria, descricao, valor_estimado)
                VALUES (%s, %s, %s, %s, %s)
            """

            valores = (
                current_user.id,
                nome,
                categoria,
                descricao,
                valor
            )

            cursor.execute(comando, valores)
            conexao.commit()

            flash("Serviço cadastrado com sucesso!", "success")
            return redirect(url_for("painel"))

        except Exception as erro:
            if conexao:
                conexao.rollback()

            print("Erro ao cadastrar serviço:", erro)
            flash("Ocorreu um erro ao cadastrar o serviço.", "danger")

        finally:
            if cursor:
                cursor.close()

            if conexao and conexao.is_connected():
                conexao.close()

    return render_template("servico_cadastro.html")


@app.route("/servicos")
@perfil_requerido("PRESTADOR")
def meus_servicos():

    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nome, categoria, descricao, valor_estimado
            FROM servicos
            WHERE prestador_id = %s
            ORDER BY id DESC
            """,
            (current_user.id,)
        )

        servicos = cursor.fetchall()

        return render_template(
            "meus_servicos.html",
            servicos=servicos
        )

    except Exception as erro:
        print("Erro ao consultar serviços:", erro)
        flash("Não foi possível carregar seus serviços.", "danger")
        return redirect(url_for("painel"))

    finally:
        if cursor:
            cursor.close()

        if conexao and conexao.is_connected():
            conexao.close()

@app.route("/servicos/editar/<int:servico_id>", methods=["GET", "POST"])
@perfil_requerido("PRESTADOR")
def editar_servico(servico_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nome, categoria, descricao, valor_estimado
            FROM servicos
            WHERE id = %s AND prestador_id = %s
            """,
            (servico_id, current_user.id)
        )

        servico = cursor.fetchone()

        if not servico:
            flash("Serviço não encontrado.", "warning")
            return redirect(url_for("meus_servicos"))

        if request.method == "POST":

            nome = request.form.get("nome", "").strip()
            categoria = request.form.get("categoria", "").strip()
            descricao = request.form.get("descricao", "").strip()
            valor_estimado = request.form.get("valor_estimado", "").strip()

            if not nome or not categoria or not descricao:
                flash("Preencha todos os campos obrigatórios.", "danger")
                return redirect(
                    url_for("editar_servico", servico_id=servico_id)
                )

            if valor_estimado == "":
                valor = None
            else:
                try:
                    valor = float(valor_estimado)

                    if valor < 0:
                        flash("O valor não pode ser negativo.", "danger")
                        return redirect(
                            url_for(
                                "editar_servico",
                                servico_id=servico_id
                            )
                        )

                except ValueError:
                    flash("Informe um valor válido.", "danger")
                    return redirect(
                        url_for(
                            "editar_servico",
                            servico_id=servico_id
                        )
                    )

            cursor.execute(
                """
                UPDATE servicos
                SET nome = %s,
                    categoria = %s,
                    descricao = %s,
                    valor_estimado = %s
                WHERE id = %s AND prestador_id = %s
                """,
                (
                    nome,
                    categoria,
                    descricao,
                    valor,
                    servico_id,
                    current_user.id
                )
            )

            conexao.commit()

            flash("Serviço atualizado com sucesso!", "success")
            return redirect(url_for("meus_servicos"))

        return render_template(
            "editar_servico.html",
            servico=servico
        )

    except Exception as erro:
        if conexao:
            conexao.rollback()

        print("Erro ao editar serviço:", erro)
        flash("Não foi possível editar o serviço.", "danger")
        return redirect(url_for("meus_servicos"))

    finally:
        if cursor:
            cursor.close()

        if conexao and conexao.is_connected():
            conexao.close()

@app.route("/servicos/excluir/<int:servico_id>", methods=["POST"])
@perfil_requerido("PRESTADOR")
def excluir_servico(servico_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute(
            """
            DELETE FROM servicos
            WHERE id = %s AND prestador_id = %s
            """,
            (servico_id, current_user.id)
        )

        if cursor.rowcount == 0:
            flash("Serviço não encontrado.", "warning")
            return redirect(url_for("meus_servicos"))

        conexao.commit()

        flash("Serviço excluído com sucesso!", "success")
        return redirect(url_for("meus_servicos"))

    except Exception as erro:
        if conexao:
            conexao.rollback()

        print("Erro ao excluir serviço:", erro)
        flash("Não foi possível excluir o serviço.", "danger")
        return redirect(url_for("meus_servicos"))

    finally:
        if cursor:
            cursor.close()

        if conexao and conexao.is_connected():
            conexao.close()


@app.route("/servicos/disponiveis")
@perfil_requerido("CLIENTE")
def servicos_disponiveis():

    busca = request.args.get("busca", "").strip()

    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:

        if busca:

            termo = f"%{busca}%"

            cursor.execute("""
                SELECT
                    servicos.id,
                    servicos.nome,
                    servicos.categoria,
                    servicos.descricao,
                    servicos.valor_estimado,
                    usuarios.nome AS prestador_nome
                FROM servicos
                INNER JOIN usuarios
                    ON servicos.prestador_id = usuarios.id
                WHERE servicos.nome LIKE %s
                   OR servicos.categoria LIKE %s
                   OR usuarios.nome LIKE %s
                ORDER BY servicos.id DESC
            """, (termo, termo, termo))

        else:

            cursor.execute("""
                SELECT
                    servicos.id,
                    servicos.nome,
                    servicos.categoria,
                    servicos.descricao,
                    servicos.valor_estimado,
                    usuarios.nome AS prestador_nome
                FROM servicos
                INNER JOIN usuarios
                    ON servicos.prestador_id = usuarios.id
                ORDER BY servicos.id DESC
            """)

        servicos = cursor.fetchall()

        return render_template(
            "servicos_disponiveis.html",
            servicos=servicos,
            busca=busca
        )

    except Exception as erro:
        print(f"Erro ao consultar serviços: {erro}")
        flash("Não foi possível consultar os serviços.", "danger")
        return redirect(url_for("painel"))

    finally:
        cursor.close()
        conexao.close()


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():

    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        if request.method == "POST":

            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip().lower()
            telefone = request.form.get("telefone", "").strip()

            if not nome or not email:
                flash("Nome e e-mail são obrigatórios.", "danger")
                return redirect(url_for("perfil"))

            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE email = %s AND id != %s
                """,
                (email, current_user.id)
            )

            outro_usuario = cursor.fetchone()

            if outro_usuario:
                flash("Este e-mail já está sendo utilizado.", "warning")
                return redirect(url_for("perfil"))

            cursor.execute(
                """
                UPDATE usuarios
                SET nome = %s,
                    email = %s,
                    telefone = %s
                WHERE id = %s
                """,
                (
                    nome,
                    email,
                    telefone,
                    current_user.id
                )
            )

            conexao.commit()

            current_user.nome = nome
            current_user.email = email

            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for("perfil"))

        cursor.execute(
            """
            SELECT telefone
            FROM usuarios
            WHERE id = %s
            """,
            (current_user.id,)
        )

        dados = cursor.fetchone()

        telefone = dados["telefone"] if dados else ""

        return render_template(
            "perfil.html",
            telefone=telefone
        )

    except Exception as erro:

        if conexao:
            conexao.rollback()

        print("Erro ao atualizar perfil:", erro)
        flash("Não foi possível atualizar seu perfil.", "danger")
        return redirect(url_for("painel"))

    finally:

        if cursor:
            cursor.close()

        if conexao and conexao.is_connected():
            conexao.close()            
 

if __name__ == "__main__":
    app.run(debug=True)