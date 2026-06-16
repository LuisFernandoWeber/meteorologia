from dotenv import load_dotenv
from pathlib import Path
import os

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
LOCAL_LOGS= "logs"
