from pony.orm import Required, Set
from datetime import datetime
from core.database import db

class Origem(db.Entity):
    tipo = Required(str)
    hora_recebido = Required(datetime)
    Leitura = Set("Leitura")
    