from pony.orm import Required
from decimal import Decimal
from datetime import datetime
from core.database import db
from models.Sensor import Sensor
from models.Origem import Origem


class Leitura(db.Entity):
    valor = Required(Decimal, scale=2)
    horario = Required(datetime)
    sensor = Required(Sensor)
    origem = Required(Origem)
