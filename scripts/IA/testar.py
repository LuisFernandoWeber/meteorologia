import os

import joblib
import numpy as np
import pandas as pd
import torch

from scripts.IA import dados
from IA.modelo import Net
from models import *

from scripts.IA.config import CAMINHO_MODELO, CAMINHO_SCALER_X, CAMINHO_SCALER_Y, CAMINHO_RESULTADO
from scripts.IA.config import COLUNAS_ENTRADA,  UNIDADE_ALVO


# --- Separar os dados de teste ---
def separar_dados(df):
    # 15% dos dados restantes destinados ao treinamento 
    total = len(df)

    indice_validacao = int(total * 0.85)

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

    df = dados.carregar_dados()
    df = dados.preparar_dados(df)
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
    main()
