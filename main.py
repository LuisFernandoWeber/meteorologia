from core.database import db
from pony.orm import db_session
from models import *
from services.importarCSV import ImportarCSV

db.generate_mapping(create_tables=False)




"""
    Importar tabelas Estacão Caçador
""" 
#Rodar bot da ANA (que salvará o arquivo no import)

#Salvar dados
try:
    ImportarCSV(nome_estacao="Estacao IFSC Cacador").executar()
except Exception as erro:
    print(f"ERRO: {erro}")


print("Sistema rodado com sucesso")
