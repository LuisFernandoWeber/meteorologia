from app.models.estado import estado

@db_session
def create_estado(nome, sigla):
    return Estado(name=nome, sigla=sigla)
