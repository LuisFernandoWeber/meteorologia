from pony.orm import Required, Set
from core.database import db
from models.Estado import Estado


class Regiao(db.Entity):
    nome = Required(str)
    estado = Required(Estado)
    cidade = Set("Cidade")
