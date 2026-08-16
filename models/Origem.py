from pony.orm import Required, Optional, Set
from core.database import db

class Origem(db.Entity):
    tipo = Required(str)
    formato = Required(str)
    descricao = Optional(str)
    leitura = Set("Leitura")

