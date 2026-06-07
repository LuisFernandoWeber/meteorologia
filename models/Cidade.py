from pony.orm import Required, Set
from core.database import db
from models.Regiao import Regiao


class Cidade(db.Entity):
    nome = Required(str)
    regiao = Required(Regiao)
    estacao = Set("Estacao")