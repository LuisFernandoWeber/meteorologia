import pandas as pd
from pony.orm import db_session, select
from core.database import db
from models import *
from scripts.IA.config import NOME_ESTACAO, COLUNAS_ENTRADA, DATA_ALVO, COLUNA_ALVO


# --- Carregar os dados do Banco ---
@db_session
def carregar_dados():
    db.generate_mapping(create_tables=False)
    estacao = Estacao.get(nome=NOME_ESTACAO)

    if not estacao:
        raise ValueError(
            f"Estação '{NOME_ESTACAO}' não encontrada no banco de dados."
        )


    consulta = select(
        (
            leitura.horario,
            leitura.sensor.nome_original,
            leitura.valor
        )
        for leitura in Leitura
        if leitura.sensor.estacao == estacao
        and leitura.sensor.nome_original in COLUNAS_ENTRADA
    )

    dados = list(consulta)
    if not dados:
        raise ValueError(
            f"Nenhuma leitura encontrada para a estação "
            f"'{NOME_ESTACAO}'."
        )

    # Transformamos o resultado do PonyORM em DataFrame.
    df = pd.DataFrame(
        dados,
        columns=[
            "Date (America/Fortaleza)",
            "sensor",
            "valor"
        ]
    )

    # Garantimos que os valores sejam numéricos.
    df["valor"] = df["valor"].astype(float)

    df = df.pivot(
        index="Date (America/Fortaleza)",
        columns="sensor",
        values="valor"
    ).reset_index()

    df.columns.name = None

    return df


# --- Preparar os dados ---
def preparar_dados(df):
    # Ordenar o df
    df = df.sort_values(
        "Date (America/Fortaleza)"
    ).reset_index(drop=True)

    # Criar a data alvo
    df["Data Alvo"] = (
        df["Date (America/Fortaleza)"]
        + pd.Timedelta(days=DATA_ALVO)
    )


    # Criar a tabela com alvos futuro
    tabela_alvo = df[
        [
            "Date (America/Fortaleza)",
            COLUNA_ALVO
        ]
    ].copy()

    tabela_alvo = tabela_alvo.rename(
        columns={
            "Date (America/Fortaleza)": "Data Alvo",
            COLUNA_ALVO: "Alvo Futuro"
        }
    )

    # Juntar os dados
    df = df.merge(
        tabela_alvo,
        on="Data Alvo",
        how="left"
    )

    # Remover registros errados
    df = df.dropna(
        subset=COLUNAS_ENTRADA + ["Alvo Futuro"]
    )

    # Ordenamos novamente depois do merge.
    df = df.sort_values(
        "Date (America/Fortaleza)"
    ).reset_index(drop=True)

    return df

