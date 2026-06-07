from pony.orm import Required, LongStr, Set
from core.database import db
from models.Estacao import Estacao


class Sensor(db.Entity):
    nome = Required(str)
    unidade_medida = Required(str)
    descricao = Required(LongStr)
    ativa = Required(bool, default=True)
    estacao = Required(Estacao)
    leitura = Set("Leitura")
    