from pony.orm import Required, Set
from datetime import date
from core.database import db
from models.Cidade import Cidade


class Estacao(db.Entity):
    nome = Required(str)
    ativo = Required(bool, default=True)
    data_ativacao = Required(date)
    elevacao = Required(str)
    cordenadas = Required(str)
    cidade = Required(Cidade)
    sensor = Set("Sensor")