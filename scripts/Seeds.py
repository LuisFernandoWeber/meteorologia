from pony.orm import db_session
from models.Estado import Estado


def executar():
    seed_estado()


#Estado
def seed_estado():
    estado = [
        ("Santa Catarina", "SC"),
        ("Rio Grande do Sul", "RS"),
        ("Paraná", "PR")
    ]

    for nome, sigla in estado:
        if not Estado.get(sigla=sigla):
            Estado(nome=nome, sigla=sigla)


if __name__ == "__main__":
    executar()