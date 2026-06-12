from datetime import datetime

class Leitura:
    def __init__(self, sensor, valor):
        self.sensor = sensor
        self.valor = valor
        self.horario = datetime.now()