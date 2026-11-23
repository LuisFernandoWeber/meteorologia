from dotenv import load_dotenv
from pathlib import Path
import os
import logging

#Le o arquivo .env
load_dotenv()


#Dados do banco de dados
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


#Variáveis
LOCAL_IMPORT = Path("imports") 
LOCAL_IMPORT.mkdir(parents=True, exist_ok=True)
LOCAL_LOGS = Path("logs")
LOCAL_LOGS.mkdir(parents=True, exist_ok=True)

# Configuração do Logging
logging.basicConfig(
    filename = LOCAL_LOGS / "sistema.log",
    filemode = "a",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(name)s.%(funcName)s - %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)