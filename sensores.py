
class Sensor:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def ler_dados(self):
        return f"Sensor {self.tipo} lendo valor: {self.valor}"

class EstacaoMeteorologica:
    def __init__(self):
        self.sensores = []

    def adicionar_sensor(self, sensor):
        self.sensores.append(sensor)

    def ler_todos_sensores(self):
        for sensor in self.sensores:
            print(sensor.ler_dados())

# Exemplo de uso
estacao = EstacaoMeteorologica()
estacao.adicionar_sensor(Sensor("Temperatura", "25°C"))
estacao.adicionar_sensor(Sensor("Umidade", "60%"))
estacao.adicionar_sensor(Sensor("Pressão", "1013 hPa"))

estacao.ler_todos_sensores()
