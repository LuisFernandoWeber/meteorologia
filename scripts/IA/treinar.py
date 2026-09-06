import os

import pandas as pd
import joblib
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import MinMaxScaler

from scripts.IA import dados
from IA.modelo import Net
from models import *

from scripts.IA.config import NUM_EPOCAS, BATCH_SIZE, LEARNING_RATE
from scripts.IA.config import CAMINHO_BASE, CAMINHO_MODELO, CAMINHO_SCALER_X, CAMINHO_SCALER_Y
from scripts.IA.config import COLUNAS_ENTRADA, UNIDADE_ALVO 


# --- Separar os dados ---
def separar_dados(df: pd.DataFrame):
    """
    70% treinamento 
    15% validação
    15% teste
    """

    total = len(df)

    indice_treino = int(total * 0.70)
    indice_validacao = int(total * 0.85)

    df_treino = df.iloc[:indice_treino].copy()
    df_validacao = df.iloc[indice_treino:indice_validacao].copy()
    df_teste = df.iloc[indice_validacao:].copy()

    return (
            df_treino,
            df_validacao,
            df_teste
        )


# --- Normalização ---
def normalizar_dados(
    df_treino,
    df_validacao,
    df_teste
):
    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()

    # ENTRADAS
    X_treino = scaler_x.fit_transform(
        df_treino[COLUNAS_ENTRADA]
    )

    X_validacao = scaler_x.transform(
        df_validacao[COLUNAS_ENTRADA]
    )

    X_teste = scaler_x.transform(
        df_teste[COLUNAS_ENTRADA]
    )    

    # SAIDAS
    y_treino = scaler_y.fit_transform(
        df_treino[["Alvo Futuro"]]
    )

    y_validacao = scaler_y.transform(
        df_validacao[["Alvo Futuro"]]
    )

    y_teste = scaler_y.transform(
        df_teste[["Alvo Futuro"]]
    )

    return (
        X_treino,
        y_treino,
        X_validacao,
        y_validacao,
        X_teste,
        y_teste,
        scaler_x,
        scaler_y
    )


# --- Data Loadrers ---
def criar_dataloader(X, y, embaralhar):
    X_tensor = torch.tensor(
        X,
        dtype=torch.float32
    )

    y_tensor = torch.tensor(
        y,
        dtype=torch.float32
    )

    dataset = TensorDataset(
        X_tensor,
        y_tensor
    )

    return DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=embaralhar
    )


# --- Treinamento ---
def treinar_modelo(
    modelo,
    train_loader,
    valid_loader
):

    # MSE - regrá de erro
    loss_fn = nn.MSELoss()

    # Otimizador - ajusta os pesos da rede para reduzir os erros
    otimizador = torch.optim.Adam(
        modelo.parameters(),
        lr=LEARNING_RATE
    )

    # Guardaremos o menor erro de validação encontrado.
    melhor_loss_validacao = float("inf")

    # Guardaremos os pesos correspondentes ao melhor modelo.
    melhor_estado = None

    for epoca in range(NUM_EPOCAS):

        # MODO TREINAMENTO
        modelo.train()

        perda_treino = 0.0

        for X_batch, y_batch in train_loader:

            # a rede "chuta" uma previsão
            pred = modelo(X_batch)

            # mede o quão errado foi o chute
            loss = loss_fn(
                pred,
                y_batch
            )

            # limpa os "ajustes" da rodada anterior
            otimizador.zero_grad()

            # calcula em que direção ajustar cada peso
            loss.backward()

            # Atualizamos os pesos da rede.
            otimizador.step()

            perda_treino += loss.item()

        perda_treino /= len(train_loader)


        # MODO VALIDAÇÃO
        modelo.eval()

        perda_validacao = 0.0

        # Durante validação não precisamos calcular gradientes.
        with torch.no_grad():

            for X_batch, y_batch in valid_loader:

                pred = modelo(X_batch)

                loss = loss_fn(
                    pred,
                    y_batch
                )

                perda_validacao += loss.item()

        perda_validacao /= len(valid_loader)

        # Mostra o progresso.
        print(
            f"Época {epoca + 1:03d}/{NUM_EPOCAS} "
            f"| Treino: {perda_treino:.6f} "
            f"| Validação: {perda_validacao:.6f}"
        )


        # SALVAR O MELHOR MODELO
        if perda_validacao < melhor_loss_validacao:

            melhor_loss_validacao = perda_validacao

            # clone() é importante para guardar uma cópia
            # independente dos pesos atuais.
            melhor_estado = {
                chave: valor.detach().cpu().clone()
                for chave, valor
                in modelo.state_dict().items()
            }

    # Depois de todas as épocas, restauramos o melhor modelo.
    modelo.load_state_dict(melhor_estado)

    return modelo


# --- Avaliar Modelo ---
def avaliar_modelo(
    modelo,
    X_teste,
    y_teste,
    scaler_y
):
    modelo.eval()

    X_tensor = torch.tensor(
        X_teste,
        dtype=torch.float32
    )

    with torch.no_grad():

        predicoes = modelo(
            X_tensor
        ).numpy()

    # Voltamos da escala 0-1 para a unidade original (hPa).
    predicoes_real = scaler_y.inverse_transform(
        predicoes
    )

    valores_reais = scaler_y.inverse_transform(
        y_teste
    )

    # Erro absoluto médio.
    mae = np.mean(
        np.abs(
            predicoes_real - valores_reais
        )
    )

    # Raiz do erro quadrático médio.
    rmse = np.sqrt(
        np.mean(
            (predicoes_real - valores_reais) ** 2
        )
    )

    print()
    print("========== RESULTADO FINAL ==========")
    print(f"MAE : {mae:.2f} {UNIDADE_ALVO}")
    print(f"RMSE: {rmse:.2f} {UNIDADE_ALVO}")

    return mae, rmse





# --- Ponto de Entrada ---

def main():

    print("Iniciando treinamento...")
    print()

    df = dados.carregar_dados()
    print(f"Registros carregados: {len(df)}")

    df = dados.preparar_dados(df)
    print(f"Registros após preparação: {len(df)}")

    # 3. SEPARAR
    (
        df_treino,
        df_validacao,
        df_teste
    ) = separar_dados(df)
    print(f"Treino:     {len(df_treino)}")
    print(f"Validação:  {len(df_validacao)}")
    print(f"Teste:      {len(df_teste)}")

    # 4. NORMALIZAR
    (
        X_treino,
        y_treino,
        X_validacao,
        y_validacao,
        X_teste,
        y_teste,
        scaler_x,
        scaler_y
    ) = normalizar_dados(
        df_treino,
        df_validacao,
        df_teste
    )

    # 5. CRIAR DATA LOADERS
    train_loader = criar_dataloader(
        X_treino,
        y_treino,
        embaralhar=True
    )

    valid_loader = criar_dataloader(
        X_validacao,
        y_validacao,
        embaralhar=False
    )

    # 6. CRIAR MODELO
    modelo = Net(
        input_dim=len(COLUNAS_ENTRADA),

        hidden_dim=64,

        num_blocos=3,

        dropout=0.3,

        # Para regressão de pressão atmosférica:
        # NÃO usamos Sigmoid na saída.
        saida_sigmoid=False
    )

    print()
    print("Modelo criado.")
    print()

    # 7. TREINAR
    modelo = treinar_modelo(
        modelo,
        train_loader,
        valid_loader
    )

    # 8. TESTAR
    avaliar_modelo(
        modelo,
        X_teste,
        y_teste,
        scaler_y
    )

    # 9. CRIAR PASTA AI
    os.makedirs(
        CAMINHO_BASE,
        exist_ok=True
    )

    # 10. SALVAR MODELO
    torch.save(
        modelo.state_dict(),
        CAMINHO_MODELO
    )

    # 11. SALVAR SCALERS
    joblib.dump(
        scaler_x,
        CAMINHO_SCALER_X
    )

    joblib.dump(
        scaler_y,
        CAMINHO_SCALER_Y
    )

    print()
    print("======================================")
    print("TREINAMENTO CONCLUÍDO")
    print("======================================")
    print()
    print(
        f"Modelo salvo em: {CAMINHO_MODELO}"
    )
    print(
        f"Scaler X salvo em: {CAMINHO_SCALER_X}"
    )
    print(
        f"Scaler Y salvo em: {CAMINHO_SCALER_Y}"
    )



if __name__ == "__main__":
    main()
    