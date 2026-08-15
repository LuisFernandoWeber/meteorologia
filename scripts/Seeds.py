from pony.orm import db_session
from models import *

"""
    Seeds responsável por inserir os dados básicos no
    banco de dados na implementação do sistema.
    Esse aquivo é usado pelo scripts/migrate para após que
    seja craido o banco ser executado a seeds.py
"""


# --- Fluxo de execução ---

def executar():
    seed_estado()
    seed_cidade()
    seed_estacao()


# --- Seeds ---

#Estado
@db_session
def seed_estado():
    estados = [
        ("Acre", "AC"),
        ("Alagoas", "AL"),
        ("Amapá", "AP"),
        ("Amazonas", "AM"),
        ("Bahia", "BA"),
        ("Ceará", "CE"),
        ("Distrito Federal", "DF"),
        ("Espírito Santo", "ES"),
        ("Goiás", "GO"),
        ("Maranhão", "MA"),
        ("Mato Grosso", "MT"),
        ("Mato Grosso do Sul", "MS"),
        ("Minas Gerais", "MG"),
        ("Pará", "PA"),
        ("Paraíba", "PB"),
        ("Paraná", "PR"),
        ("Pernambuco", "PE"),
        ("Piauí", "PI"),
        ("Rio de Janeiro", "RJ"),
        ("Rio Grande do Norte", "RN"),
        ("Rio Grande do Sul", "RS"),
        ("Rondônia", "RO"),
        ("Roraima", "RR"),
        ("Santa Catarina", "SC"),
        ("São Paulo", "SP"),
        ("Sergipe", "SE"),
        ("Tocantins", "TO"),
    ]

    for nome, sigla in estados:
        if not Estado.get(sigla=sigla):
            Estado(nome=nome, sigla=sigla)


#Cidade
@db_session
def seed_cidade():
    cidades = [
        ("Caçador", "SC",),
    ]

    for nome, sigla_estado in cidades:
        if not Cidade.get(nome=nome):
            estado = Estado.get(sigla = sigla_estado)
            Cidade(nome=nome, estado=estado)


#Estacao
@db_session
def seed_estacao():
    estacoes = [
        ("Estacao IFSC Cacador", "2026-06-14", "920.0", "26° 46\' 47\" S  51° 2\' 16\" W", "Caçador")
    ]

    for nome, data_ativacao, elevacao, cordenadas, nome_cidade in estacoes:
        if not Estacao.get(nome=nome):
            cidade = Cidade.get(nome=nome_cidade)
            Estacao(
                nome=nome, 
                data_ativacao=data_ativacao,
                elevacao = elevacao,
                cordenadas = cordenadas,
                cidade = cidade
            )


# --- Ponto de entrada ---

if __name__ == "__main__":
    executar()
