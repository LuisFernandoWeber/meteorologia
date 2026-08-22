import os

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from pony.orm import db_session, select

from core.database import db
from models import *

from AI.modelo import Net

"""
    previsao_pressao_atmosfera.py é responsável por treinar o modelo
    de rede neural (AI/modelo.py) que prevê a pressão atmosférica do
    dia seguinte, a partir das leituras já salvas no banco de dados.

    Este script é executado manualmente e de forma individual (fora
    do fluxo principal do sistema), apenas para gerar os arquivos de
    treinamento (modelo + scalers) que depois serão levados para a
    produção.

    [ALTERAÇÃO] Antes os dados de treinamento vinham de um arquivo
    CSV solto (era só um exemplo, como já estava comentado aqui).
    Agora eles são consultados diretamente do banco de dados através
    do Pony ORM, já que o sistema passou a salvar tudo por lá.
"""


# ============================================================
# CONFIGURAÇÕES DO TREINAMENTO
# ============================================================

# Quantidade de épocas.
NUM_EPOCAS = 100

# Quantos registros serão processados de uma vez.
BATCH_SIZE = 64

# Taxa de aprendizado do Adam.
LEARNING_RATE = 0.0001

# [ALTERAÇÃO] Antes os dados vinham de um único arquivo CSV, então
# não existia a necessidade de indicar de qual estação eram os dados.
# Agora que tudo está no banco (e pode haver mais de uma estação
# cadastrada), precisamos dizer explicitamente de qual estação
# queremos buscar as leituras.
NOME_ESTACAO = "Estacao IFSC Cacador"

# Nome dos arquivos que receberemos como saída.
# [ALTERAÇÃO] Renomeados de "temperatura" para "pressao", já que
# este script (agora previsao_pressao_atmosfera.py) é especificamente
# sobre a previsão da pressão atmosférica.
CAMINHO_MODELO = "AI/modelo_pressao_atmosferica.pth"
CAMINHO_SCALER_X = "AI/scaler_x_pressao.pkl"
CAMINHO_SCALER_Y = "AI/scaler_y_pressao.pkl"

# [ALTERAÇÃO] Usada apenas para exibir o resultado final (MAE/RMSE)
# com a unidade correta, já que antes estava fixo em "°C".
UNIDADE_ALVO = "hPa"


# ============================================================
# COLUNAS UTILIZADAS PELA IA
# ============================================================
#
# Esses nomes precisam ser IDÊNTICOS ao "nome_original" cadastrado
# na tabela Sensor, pois são usados diretamente na consulta ao
# banco de dados (ver carregar_dados).

COLUNAS_ENTRADA = [
    "Atmospheric pressure (hPa)",
    "Temperature (°C)",
    "Humidity (%)",
    "Average wind speed (m/s)",
    "Rain (mm)",
    "Dew point (°C)",
]

# Queremos prever a pressão atmosférica.
COLUNA_ALVO = "Atmospheric pressure (hPa)"


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

@db_session
def carregar_dados():
    """
    Carrega os dados que serão utilizados para treinamento.

    [ALTERAÇÃO] Esta função antes lia os dados de um arquivo CSV
    (era só um exemplo, como já estava comentado aqui). Agora ela
    consulta o banco de dados diretamente através do Pony ORM.

    Buscamos na tabela Leitura apenas os registros cujo sensor
    pertence à estação NOME_ESTACAO e cujo nome_original está entre
    as COLUNAS_ENTRADA. A coluna "origem" é ignorada, conforme
    combinado, pois é só documentação e não interfere no resultado.

    Os dados chegam do banco no formato "longo" (uma linha por
    leitura: horário, sensor, valor). Como o restante do script foi
    escrito pensando no formato "largo" (uma coluna por sensor, igual
    ao CSV antigo), já aproveitamos aqui e giramos a tabela (pivot)
    antes de devolver o DataFrame.
    """

    estacao = Estacao.get(nome=NOME_ESTACAO)

    if not estacao:
        raise ValueError(
            f"Estação '{NOME_ESTACAO}' não encontrada no banco de dados"
        )

    # Busca (horário, nome do sensor, valor) de todas as leituras da
    # estação, somente para os sensores usados como entrada da IA.
    consulta = select(
        (leitura.horario, leitura.sensor.nome_original, leitura.valor)
        for leitura in Leitura
        if leitura.sensor.estacao == estacao
        and leitura.sensor.nome_original in COLUNAS_ENTRADA
    )

    dados = list(consulta)

    if not dados:
        raise ValueError(
            f"Nenhuma leitura encontrada para a estação '{NOME_ESTACAO}' "
            "com os sensores configurados em COLUNAS_ENTRADA"
        )

    df = pd.DataFrame(
        dados,
        columns=["Date (America/Fortaleza)", "sensor", "valor"]
    )

    # O valor vem do banco como Decimal (para manter a precisão).
    # Convertemos para float para trabalharmos com numpy/sklearn/torch.
    df["valor"] = df["valor"].astype(float)

    # Gira a tabela: cada sensor vira uma coluna e cada horário
    # uma linha, reproduzindo o mesmo formato "largo" do CSV antigo.
    #
    # Isso só funciona corretamente porque, na importação (ver
    # scripts/importarCSV.py), todos os sensores de uma mesma linha
    # do CSV original recebem exatamente o mesmo "horario" no banco.
    # Se no futuro passarmos a ter fontes onde cada sensor grava seu
    # próprio horário de forma independente (ex.: dispositivos Lora),
    # essa junção por horário pode gerar linhas fragmentadas/NaN e
    # essa parte precisará ser revista.
    df = df.pivot(
        index="Date (America/Fortaleza)",
        columns="sensor",
        values="valor"
    ).reset_index()

    df.columns.name = None

    return df


# ============================================================
# PREPARAÇÃO DOS DADOS
# ============================================================

def preparar_dados(df):
    """
    Prepara os dados para o treinamento.

    Aqui fazemos:
    1. Seleção das colunas
    2. Conversão da data
    3. Criação do alvo
    4. Remoção de registros sem alvo
    """

    # Criamos uma cópia para evitar problemas do tipo
    # SettingWithCopyWarning que apareceu no seu notebook.
    #
    # [ALTERAÇÃO] Como carregar_dados() já filtra os sensores no
    # banco, esta seleção passa a funcionar mais como uma garantia
    # da ordem/presença das colunas do que como um filtro novo.
    df = df[
        [
            "Date (America/Fortaleza)",
            *COLUNAS_ENTRADA
        ]
    ].copy()

    # [ALTERAÇÃO] Os dados agora já vêm do banco como objetos datetime
    # nativos do Python (não como texto), então não precisamos mais
    # informar o "format" que era usado para interpretar as datas do
    # CSV. O pd.to_datetime aqui só garante que a coluna fique com o
    # dtype correto do pandas.
    df["Date (America/Fortaleza)"] = pd.to_datetime(
        df["Date (America/Fortaleza)"]
    )

    # --------------------------------------------------------
    # CRIAÇÃO DO ALVO
    # --------------------------------------------------------
    #
    # Queremos prever o valor de COLUNA_ALVO (pressão atmosférica)
    # do mesmo horário no dia seguinte.
    #
    # Exemplo:
    #
    # 10/08 15:00 → entradas
    #
    #                      ↓
    #
    # 11/08 15:00 → pressão atmosférica que queremos prever
    #
    # [ALTERAÇÃO] Essa seção antes usava a coluna "Temperature (°C)"
    # fixa no código, mesmo com COLUNA_ALVO apontando para a pressão
    # atmosférica. Na prática isso fazia o alvo usado lá na frente
    # (em normalizar_dados) ser o valor de COLUNA_ALVO NO MESMO
    # horário da entrada — ou seja, o próprio valor de pressão atual
    # (que já está entre as COLUNAS_ENTRADA) acabava sendo usado como
    # resposta ao mesmo tempo, o que não fazia sentido para o
    # treinamento. Aqui a lógica foi generalizada para usar
    # COLUNA_ALVO dinamicamente, então o alvo passa a ser
    # corretamente o valor do dia seguinte.
    #

    df["Data Alvo"] = (
        df["Date (America/Fortaleza)"]
        + pd.Timedelta(days=1)
    )

    # Criamos uma tabela contendo:
    #
    # data/hora -> valor de COLUNA_ALVO
    #
    # Isso permite encontrar rapidamente o valor de COLUNA_ALVO
    # correspondente ao dia seguinte.
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

    # Fazemos um merge para encontrar o valor futuro.
    df = df.merge(
        tabela_alvo,
        on="Data Alvo",
        how="left"
    )

    # --------------------------------------------------------
    # REMOVER REGISTROS SEM ALVO
    # --------------------------------------------------------
    #
    # Os últimos registros do período não possuem o valor do dia
    # seguinte dentro do conjunto de dados.
    #
    # Não devemos "inventar" esses valores usando interpolate().
    #
    # No seu notebook você utilizava interpolate(), mas isso
    # pode criar um alvo artificial.
    #
    df = df.dropna(
        subset=COLUNAS_ENTRADA + ["Alvo Futuro"]
    )

    # Garantimos que os dados estejam ordenados cronologicamente.
    df = df.sort_values(
        "Date (America/Fortaleza)"
    ).reset_index(drop=True)

    return df


# ============================================================
# SEPARAÇÃO DOS DADOS
# ============================================================

def separar_dados(df):
    """
    Divide os dados em:

        70% treinamento
        15% validação
        15% teste

    Como estamos trabalhando com uma série temporal,
    NÃO embaralhamos os registros.

    Exemplo:

        Janeiro ---------------- Agosto
                  TREINAMENTO

        Setembro -------- Outubro
                    VALIDAÇÃO

        Novembro ------- Dezembro
                      TESTE
    """

    total = len(df)

    indice_treino = int(total * 0.70)
    indice_validacao = int(total * 0.85)

    df_treino = df.iloc[:indice_treino].copy()

    df_validacao = df.iloc[
        indice_treino:indice_validacao
    ].copy()

    df_teste = df.iloc[
        indice_validacao:
    ].copy()

    return (
        df_treino,
        df_validacao,
        df_teste
    )


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_dados(
    df_treino,
    df_validacao,
    df_teste
):
    """
    Normaliza os dados utilizando MinMaxScaler.

    ATENÇÃO:

    O scaler deve ser ajustado SOMENTE utilizando os dados
    de treinamento.

    Depois:

        treino     -> fit_transform()
        validação  -> transform()
        teste      -> transform()

    Isso evita que informações do futuro "vazem" para o
    treinamento.
    """

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()

    # ----------------------------
    # ENTRADAS
    # ----------------------------

    X_treino = scaler_x.fit_transform(
        df_treino[COLUNAS_ENTRADA]
    )

    X_validacao = scaler_x.transform(
        df_validacao[COLUNAS_ENTRADA]
    )

    X_teste = scaler_x.transform(
        df_teste[COLUNAS_ENTRADA]
    )

    # ----------------------------
    # SAÍDA
    # ----------------------------

    # [ALTERAÇÃO] Usamos "Alvo Futuro" (criado em preparar_dados) em
    # vez de COLUNA_ALVO diretamente — ver comentário na criação do
    # alvo para entender o motivo da mudança.
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


# ============================================================
# DATA LOADERS
# ============================================================

def criar_dataloader(X, y, embaralhar):
    """
    Converte os dados para tensores PyTorch e cria um
    DataLoader.

    O DataLoader divide os dados em mini-batches.

    Exemplo com BATCH_SIZE = 64:

        64 registros
        ↓
        rede
        ↓
        calcula erro
        ↓
        atualiza pesos

    """

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


# ============================================================
# TREINAMENTO
# ============================================================

def treinar_modelo(
    modelo,
    train_loader,
    valid_loader
):
    """
    Treina a rede neural.

    Também acompanha o erro de validação.

    O modelo salvo será aquele que apresentar o melhor
    resultado na validação, e não simplesmente o último
    modelo produzido pela última época.
    """

    # MSE é apropriado para regressão.
    loss_fn = nn.MSELoss()

    # Adam é o otimizador que já estava sendo utilizado
    # no seu notebook.
    otimizador = torch.optim.Adam(
        modelo.parameters(),
        lr=LEARNING_RATE
    )

    # Guardaremos o menor erro de validação encontrado.
    melhor_loss_validacao = float("inf")

    # Guardaremos os pesos correspondentes ao melhor modelo.
    melhor_estado = None

    for epoca in range(NUM_EPOCAS):

        # ====================================================
        # MODO TREINAMENTO
        # ====================================================

        modelo.train()

        perda_treino = 0.0

        for X_batch, y_batch in train_loader:

            # Fazemos a previsão.
            pred = modelo(X_batch)

            # Comparamos previsão x valor verdadeiro.
            loss = loss_fn(
                pred,
                y_batch
            )

            # Zeramos os gradientes da iteração anterior.
            otimizador.zero_grad()

            # Calculamos os gradientes.
            loss.backward()

            # Atualizamos os pesos da rede.
            otimizador.step()

            perda_treino += loss.item()

        perda_treino /= len(train_loader)

        # ====================================================
        # MODO VALIDAÇÃO
        # ====================================================

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

        # ====================================================
        # SALVAR O MELHOR MODELO
        # ====================================================

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


# ============================================================
# AVALIAÇÃO FINAL
# ============================================================

def avaliar_modelo(
    modelo,
    X_teste,
    y_teste,
    scaler_y
):
    """
    Avalia o modelo utilizando o conjunto de TESTE.

    O teste é utilizado somente depois que terminamos
    de escolher o modelo.

    Aqui calculamos o erro na unidade do alvo (UNIDADE_ALVO).
    """

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


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("Iniciando treinamento...")
    print()

    # --------------------------------------------------------
    # 1. CARREGAR
    # --------------------------------------------------------

    df = carregar_dados()

    print(
        f"Registros carregados: {len(df)}"
    )

    # --------------------------------------------------------
    # 2. PREPARAR
    # --------------------------------------------------------

    df = preparar_dados(df)

    print(
        f"Registros após preparação: {len(df)}"
    )

    # --------------------------------------------------------
    # 3. SEPARAR
    # --------------------------------------------------------

    (
        df_treino,
        df_validacao,
        df_teste
    ) = separar_dados(df)

    print(
        f"Treino:     {len(df_treino)}"
    )

    print(
        f"Validação:  {len(df_validacao)}"
    )

    print(
        f"Teste:      {len(df_teste)}"
    )

    # --------------------------------------------------------
    # 4. NORMALIZAR
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 5. CRIAR DATA LOADERS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 6. CRIAR MODELO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 7. TREINAR
    # --------------------------------------------------------

    modelo = treinar_modelo(
        modelo,
        train_loader,
        valid_loader
    )

    # --------------------------------------------------------
    # 8. TESTAR
    # --------------------------------------------------------

    avaliar_modelo(
        modelo,
        X_teste,
        y_teste,
        scaler_y
    )

    # --------------------------------------------------------
    # 9. CRIAR PASTA AI
    # --------------------------------------------------------

    os.makedirs(
        "AI",
        exist_ok=True
    )

    # --------------------------------------------------------
    # 10. SALVAR MODELO
    # --------------------------------------------------------

    torch.save(
        modelo.state_dict(),
        CAMINHO_MODELO
    )

    # --------------------------------------------------------
    # 11. SALVAR SCALERS
    # --------------------------------------------------------

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


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    # [ALTERAÇÃO] Como este script é executado individualmente
    # (fora do fluxo principal do sistema), precisamos gerar o
    # mapeamento das entidades do Pony ORM antes de consultar o
    # banco. create_tables=False porque as tabelas já existem
    # (foram criadas pelo scripts/migrate.py).
    db.generate_mapping(create_tables=False)
    main()
    