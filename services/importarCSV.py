from pathlib import Path
from datetime import datetime
from io import StringIO
import pandas as pd
from core.config import LOCAL_IMPORT, LOCAL_LOGS
from models import *
from core.database import db
from pony.orm import db_session
from decimal import Decimal


db.generate_mapping(create_tables=False) 

#Verificar os arquivos contidos na pasta import
arquivos = [arquivo for arquivo in LOCAL_IMPORT.iterdir() if arquivo.is_file()]

if not arquivos:
    print("Nenhum arquivo encontrado")

    #Somente proceguir caso a quantidade de arquivo ser igual a 1
if len(arquivos) == 1:
    arquivo = arquivos[0]

    nome = arquivo.stem
    formato = arquivo.suffix

    print(nome, formato)    

    if formato != ".csv":
        print("formato não válido")
        #Parar de executar


    #Esse else deve ser provisório. depois podemos quebrar o programa na validação ali de cima:
    else:

        #Normalizar o arquivo
        lista_normalizada = list()
        with open(f"{LOCAL_IMPORT}/{nome}{formato}", "r", encoding="utf-16-le") as file:
            for count, linha in enumerate(file):
                # Verificar quantas colunas tem a partir do cabeçalho
                if count == 0:
                    quantidade = linha.count(";")

                #Salvar as linhas corretas
                if linha.count(";") == quantidade:
                    lista_normalizada.append(linha)
                else:
                    """
                        PROVIsÓRIO - Depois devo jogar em um arquivo de logs
                    """
                    print(f"{datetime.now()} {count+1} -> {linha}")

        data_io = StringIO("".join(lista_normalizada))



        #Carregar o dataset do Pandas
        data = pd.read_csv(data_io, sep=";")
    


        #Criar os sensores na tabela sernsores de acordo com o nome_original
        with db_session:
            colunas = data.columns
            for cont, coluna in enumerate(colunas):
                #Ignorar a primeira linha
                if cont != 0:
                    print(coluna)
                    if not Sensor.get(nome_original = coluna):
                        Sensor(nome_original = coluna)

                

        #Salvar as medidas no banco de dados na tabela Leituras
        with db_session:
            # Garantir que os sensores existem
            colunas = data.columns
            for cont, coluna in enumerate(colunas):
                if cont != 0:
                    if not Sensor.get(nome_original=coluna):
                        Sensor(nome_original=coluna)


            # Salvar as leituras
            for _, linha in data.iterrows():
                horario = datetime.strptime(linha[colunas[0]], "%d/%m/%Y %H:%M:%S")
            
                for coluna in colunas[1:]:
                    if coluna.startswith("Unnamed"):
                        continue
                    sensor = Sensor.get(nome_original=coluna)
                    
                    # Converte o valor
                    valor_raw = str(linha[coluna]).replace(",", "").strip()
                    if valor_raw in ("", "nan", "None"):
                        continue  # pula célula vazia
                    valor = Decimal(valor_raw)

                    # Verifica se já existe leitura para esse sensor nesse horário
                    ja_existe = Leitura.get(horario=horario, sensor=sensor)
                    #ja_existe = False
                    
                    if not ja_existe:
                        Leitura(
                            valor=valor,
                            horario=horario,
                            sensor=sensor,
                            #origem=
                        )
                    else:
                        print(f"Já existe leitura: {sensor.nome_original} - {horario}")
