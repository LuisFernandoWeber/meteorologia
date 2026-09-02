import os

import joblib
import numpy as np
import pandas as pd
import torch

from pony.orm import db_session, select

from core.database import db
from models import *

from IA.modelo import Net


# --- Configurações ---
# Arquivos IA
CAMINHO_MODELO = "IA/modelo_pressao_atmosferica.pth"
CAMINHO_SCALER_X = "IA/scaler_x_pressao.pkl"
CAMINHO_SCALER_Y = "IA/scaler_y_pressao.pkl"

# Aquivo gerado por esse script
CAMINHO_RESULTADO = "IA/teste_pressao_atmosferica.csv"

#Dados
DATA_ALVO = 1
NOME_ESTACAO = "Estacao IFSC Cacador"

COLUNAS_ENTRADA = [
    "Atmospheric pressure (hPa)",
    "Temperature (°C)",
    "Humidity (%)",
    "Average wind speed (m/s)",
    "Rain (mm)",
    "Dew point (°C)",
]

COLUNA_ALVO = "Atmospheric pressure (hPa)"

UNIDADE_ALVO = "hPa"



# --- Carregar os dados do Banco ---
@db_session
def carregar_dados():
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


# --- Separar os dados de teste ---
def separar_dados(df):
    total = len(df)

    indice_validacao = int(total * 0.85)

    # Pegamos somente os últimos 15%.
    df_teste = df.iloc[indice_validacao:].copy()

    return df_teste


# --- Carregar o Modelo ---
def carregar_modelo():
    modelo = Net(
        input_dim=len(COLUNAS_ENTRADA),
        hidden_dim=64,
        num_blocos=3,
        dropout=0.3,
        saida_sigmoid=False
    )

    # Carregamos os pesos que foram salvos pelo treinamento.
    modelo.load_state_dict(
        torch.load(
            CAMINHO_MODELO,
            map_location="cpu",
            weights_only=True
        )
    )

    # Colocamos a rede em modo de avaliação.
    modelo.eval()

    return modelo


# --- Fazer a previsão ---
def fazer_previsoes(
    modelo,
    df_teste,
    scaler_x,
    scaler_y
):
    
    # Pegar apenas as entradas
    X = df_teste[
        COLUNAS_ENTRADA
    ]

    # Normalização dos dados
    X_normalizado = scaler_x.transform(X)

    # Transformar em tensores
    X_tensor = torch.tensor(
        X_normalizado,
        dtype=torch.float32
    )

    # Fazer a previsão
    with torch.no_grad():
        previsoes_normalizadas = modelo(X_tensor).numpy()

    # Inverter a normalização
    previsoes = scaler_y.inverse_transform(previsoes_normalizadas).flatten()

    # Pegamos os valores reais diretamente do DataFrame.
    valores_reais = df_teste[
        "Alvo Futuro"
    ].to_numpy()

    return (
        previsoes,
        valores_reais
    )


# --- Criar os resultados em um DataFrame ---
def criar_resultado(
    df_teste,
    previsoes,
    valores_reais
):

    resultado = pd.DataFrame()

    
    # Momento em que a previsão foi realizada.
    resultado["data_base"] = (
        df_teste["Date (America/Fortaleza)"]
        .to_numpy()
    )

    # Momento que a previsão representa.
    resultado["data_alvo"] = (
        df_teste["Data Alvo"]
        .to_numpy()
    )

    # Entrada da IA
    for coluna in COLUNAS_ENTRADA:
        nome_coluna = f"entrada_{coluna}"
        resultado[nome_coluna] = (df_teste[coluna].to_numpy())

    # Resultado reais(para comparativos)
    resultado["pressao_real_hpa"] = valores_reais

    # Resultados Gerados pela IA
    resultado["pressao_prevista_hpa"] = previsoes

    # Resultado = diferença entre o Real e o Gerado
    resultado["erro_hpa"] = (
        previsoes - valores_reais
    )

    # Erro absoluto:
    resultado["erro_absoluto_hpa"] = (
        np.abs(
            resultado["erro_hpa"]
        )
    )

    return resultado


# --- Salvar os resultados ---

def salvar_resultado(resultado):

    # Garante que a pasta IA exista.
    os.makedirs(
        "IA",
        exist_ok=True
    )

    # Salva os resultados
    resultado.to_csv(
        CAMINHO_RESULTADO,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print(
        f"Resultado salvo em: {CAMINHO_RESULTADO}"
    )


# --- Main ---
def main():

    print("Inicializando os Testes")

    df = carregar_dados()
    df = preparar_dados(df)
    df_teste = separar_dados(df)

    # Carregar Scalers
    scaler_x = joblib.load(CAMINHO_SCALER_X)
    scaler_y = joblib.load(CAMINHO_SCALER_Y)

    # Carregar modelo
    modelo = carregar_modelo()

    # Fazer previsão
    (
        previsoes,
        valores_reais
    ) = fazer_previsoes(
        modelo,
        df_teste,
        scaler_x,
        scaler_y
    )


    # Salvar resultado
    resultado = criar_resultado(df_teste, previsoes, valores_reais)
    salvar_resultado(resultado)

    print()
    print("Teste finalizado com sucesso.")
    


# Execução   
if __name__ == "__main__":
    db.generate_mapping(create_tables=False)
    main()
