from pathlib import Path
from datetime import datetime
from io import StringIO
import pandas as pd
from core.config import LOCAL_IMPORT
from models import *
from core.database import db
from pony.orm import db_session
from decimal import Decimal
from pony.orm import TransactionIntegrityError


TAMANHO_LOTE = 5000


class ImportarCSV:

    #Construtor
    @db_session
    def __init__(self, nome_estacao):
        estacao = Estacao.get(nome=nome_estacao)
        if not estacao:
            raise ValueError("Estação não encontrada")
        self.id_estacao = estacao.id
    
    def verificar_arquivo(self):
        arquivos = [arquivo for arquivo in LOCAL_IMPORT.iterdir() if arquivo.is_file()]

        #Se não tiver um arquivo
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo encontrado")

        #Somente processar caso a quantidade de arquivo ser igua a 1
        if len(arquivos) == 1:
            arquivo = arquivos[0]

            nome = arquivo.stem
            formato = arquivo.suffix   

            if formato != ".csv":
                raise ValueError(f"Formato de arquivo inválido: {formato}")

            return nome
        
        #Caso ter mais que um arquivo
        raise ValueError("Mais de um arquivo encontrado na pasta Import")

    def normalizar_arquivo_csv(self, nome_arquivo:str):
        lista_normalizada = list()

        #Carregar o arquivo
        with open(f"{LOCAL_IMPORT}/{nome_arquivo}.csv", "r", encoding="utf-16-le") as file:
            for count, linha in enumerate(file):
                
                # Verificar quantas colunas tem a partir do cabeçalho
                if count == 0:
                    quantidade = linha.count(";")
                    lista_normalizada.append(linha)
                    continue

                #Salvar as linhas corretas
                if linha.count(";") == quantidade:
                    lista_normalizada.append(linha)
                else:
                    print(f"[AVISO] Linha {count+1} ignorada (colunas inconsistentes): {linha.strip()}")

        #juntar a lista em um formato que o pandas entende
        data_io = StringIO("".join(lista_normalizada))
        return data_io

    def carregar_dataset(self, data_io):
        data = pd.read_csv(data_io, sep=";")
        data = data.loc[:, ~data.columns.str.startswith("Unnamed")] #Remove colunas vazias
        return data

    """
        Procedimento que cria os sensores na tabela sensores de acordo com o nome_original
        data_pandas: Dataset pandas carregado
    """
    @db_session
    def criar_sensores(self, data_pandas: pd.DataFrame):
        colunas = data_pandas.columns
        estacao = Estacao[self.id_estacao]

        for cont, coluna in enumerate(colunas):
            #Ignorar a primeira coluna que sempre será de data
            if cont != 0:
                #Verificar se já não foi criada e criar apenas com o atributo coluna
                if not Sensor.get(nome_original = coluna, estacao = estacao):
                    Sensor(
                        nome_original = coluna,
                        estacao = estacao
                    )

    def salvar_medidas(self, data_pandas: pd.DataFrame):
        colunas = data_pandas.columns

        # Carrega os IDs dos sensores da estação usando Pony ORM normalmente
        with db_session:
            estacao = Estacao[self.id_estacao]
            sensores = {sensor.nome_original: sensor.id for sensor in estacao.sensor}

        # Valida se todos os sensores existem
        for coluna in colunas[1:]:
            if coluna not in sensores:
                raise ValueError(f"Sensor '{coluna}' não encontrado")

        lote = []
        total_inserido = 0

        for _, linha in data_pandas.iterrows():
            horario = datetime.strptime(linha[colunas[0]], "%d/%m/%Y %H:%M:%S")

            for coluna in colunas[1:]:
                valor_raw = str(linha[coluna]).replace(",", "").strip()

                if valor_raw in ("", "nan", "None"):
                    continue

                lote.append((
                    float(valor_raw),    
                    horario,
                    sensores[coluna],     
                ))

                # Quando o lote encher, executa e limpa
                if len(lote) >= TAMANHO_LOTE:
                    total_inserido += self._executar_lote(lote)
                    lote.clear()
        
        # Executa o restante que não completou um lote
        if lote:
            total_inserido += self._executar_lote(lote)

        print(f"[INFO] Importação concluída: {total_inserido} registros inseridos.")

    @db_session
    def _executar_lote(self, lote: list) -> int:
        sql = "INSERT IGNORE INTO leitura (valor, horario, sensor) VALUES (%s, %s, %s)"
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, lote)
        conn.commit()
        inseridos = cursor.rowcount
        cursor.close()
        return inseridos

    def excluir_arquivo(self, nome_arquivo: str):
        arquivo = LOCAL_IMPORT / f"{nome_arquivo}.csv"
        arquivo.unlink()

    def executar(self):
        nome_arquivo = self.verificar_arquivo()
        data_io = self.normalizar_arquivo_csv(nome_arquivo)
        data = self.carregar_dataset(data_io)

        self.criar_sensores(data)
        self.salvar_medidas(data)
        
        self.excluir_arquivo(nome_arquivo=nome_arquivo)




if __name__ == "__main__":
    db.generate_mapping(create_tables=False)
    importador = ImportarCSV(estacao=1)
    importador.executar()

