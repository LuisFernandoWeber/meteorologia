print("Sistema meteorológico iniciado")
from sensores import Sensor
from estacao import EstacaoMeteorologica

estacao = EstacaoMeteorologica(1, "São Paulo")

sensor1 = Sensor("Temperatura", "25°C")
sensor2 = Sensor("Umidade", "60%")
sensor3 = Sensor("Pressão", "1013 hPa")

estacao.adicionar_sensor(sensor1)
estacao.adicionar_sensor(sensor2)
estacao.adicionar_sensor(sensor3)

estacao.ler_todos_sensores()