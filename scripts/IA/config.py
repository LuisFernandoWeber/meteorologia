# --- Configurações Gerais do Treinamento e Teste da IA ---

# -- Configurações do Treinamento --
# IA - Quantidade de épocas
NUM_EPOCAS = 2

# IA - Quantos registros serão processados de uma vez.
BATCH_SIZE = 64

# IA -Taxa de aprendizado do Adam.
LEARNING_RATE = 0.1


# -- Dados --
# IA - Data alvo do dia que queremos treinar (esse deve ser em dias)
DATA_ALVO = 7

# DADOS - Estação
NOME_ESTACAO = "Estacao IFSC Cacador"

# DADOS - Colunas de entrada (Esses nomes precisam ser idênticos aos nomes da tabela sensores)
COLUNAS_ENTRADA = [ 
    "Atmospheric pressure (hPa)",
    "Temperature (°C)",
    "Humidity (%)",
    "Average wind speed (m/s)",
    "Rain (mm)",
    "Dew point (°C)", 
]

# DADOS - Dado previso pela IA
COLUNA_ALVO = "Atmospheric pressure (hPa)"
UNIDADE_ALVO = "hpa"


# -- Caminhos --
# IA - Nome dos arquivos salvos pelo treinamento e carregado pelo teste 
CAMINHO_BASE = "IA/pressao_atmosferica/"
CAMINHO_MODELO = CAMINHO_BASE + "modelo.pth"
CAMINHO_SCALER_X = CAMINHO_BASE + "scaler_x.pkl"
CAMINHO_SCALER_Y = CAMINHO_BASE + "scaler_y.pkl"


# Aquivo gerado pelo script teste
CAMINHO_RESULTADO = "IA/teste_pressao_atmosferica.csv"
