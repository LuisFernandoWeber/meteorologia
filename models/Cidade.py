from pony.orm import Required, Set
from core.database import db
from models.Estado import Estado


class Cidade(db.Entity):
    nome = Required(str)
    estado = Required(Estado)
    estacao = Set("Estacao")
