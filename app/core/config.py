"""
Centraliza configurações.

Exemplo:

caminho de pastas
chaves API
constantes
banco de dados
ambiente
"""
from dotenv import load_dotenv
import os

#Le o arquivo .env
load_dotenv()

DATABASE_NAME = os.getenv("DATABASE_NAME")
