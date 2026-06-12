class EstacaoMeteorologica:

    def __init__(self, id, cidade):
        self.id = id
        self.cidade = cidade
        self.sensores = []

    def adicionar_sensor(self, sensor):
        self.sensores.append(sensor)

    def ler_todos_sensores(self):

        print(f"\nEstação da cidade: {self.cidade}")

        for sensor in self.sensores:
            print(sensor.ler_dados())