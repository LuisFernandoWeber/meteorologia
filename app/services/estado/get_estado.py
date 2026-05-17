from pony.orm import db_session
from app.models.Estado import Estado

@db_session
def get_estado_by_id(id):
    return Estado.get(id=id)

@db_session
def get_estado_by_nome(nome):
    return Estado.get(nome=nome)

@db_session
def get_estado_by_sigla(sigla):
    return Estado.get(sigla=sigla)
