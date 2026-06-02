from pony.orm import db_session
from app.models.Estado import Estado

@db_session
def create_estado(nome, sigla):
    return Estado(nome=nome, sigla=sigla)
