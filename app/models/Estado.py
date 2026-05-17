from pony.orm import Required
from app.core.database import db


class Estado(db.Entity): #Entity criar uma entidade no banco
    nome = Required(str) #Required = obrigatório
    sigla = Required(str)

