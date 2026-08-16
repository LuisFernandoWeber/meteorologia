from core.database import db
from models import *
from scripts import seeds

"""
    Migrate responsável por gerar as tabelas e rodar a
    seeds autmoaticamente. 
    Esse script deve ser rodado manualmente no ambiente virtual
    para implementação do sistema
"""


#Função de execução
def executar():
    gerar_tabelas()
    executar_seeds()


#Gerar as tabelas no banco de dados
def gerar_tabelas():
    try:
        db.generate_mapping(create_tables=True)
        print("Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar as Tabelas. Erro: {e}")

#Executar as Seeds
def executar_seeds():
    seeds.executar()


if __name__ == "__main__":
    executar()
