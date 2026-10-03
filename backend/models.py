from flask_login import UserMixin


class Usuario(UserMixin):

    def __init__(self, id, nome, email, perfil):
        self.id = id
        self.nome = nome
        self.email = email
        self.perfil = perfil