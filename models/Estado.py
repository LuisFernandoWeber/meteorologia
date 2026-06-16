from pony.orm import Required, Set
from core.database import db


class Estado(db.Entity):
    nome = Required(str)
    sigla = Required(str)
    regiao = Set("Cidade")
