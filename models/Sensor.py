from pony.orm import Required, Optional, LongStr, Set
from core.database import db
from models.Estacao import Estacao


class Sensor(db.Entity):
    nome = Optional(str)
    nome_original = Required(str)
    unidade_medida = Optional(str)
    descricao = Optional(LongStr)
    ativa = Required(bool, default=True)
    estacao = Optional(Estacao)
    leitura = Set("Leitura")
    