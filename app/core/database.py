import os
from pony.orm import Database
from app.core.config import DATABASE_NAME

# Resolve o caminho absoluto para o banco de dados
# Isso evita erros de 'unable to open database file' no Windows
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
full_db_path = os.path.join(base_path, DATABASE_NAME)

# Garante que a pasta exista (os.makedirs com exist_ok=True evita erros se já existir)
db_dir = os.path.dirname(full_db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

#criar o objeto do PonyORM
db = Database()

#Conecta no SQLite
db.bind(
    provider="sqlite",
    filename=full_db_path,
    create_db=True #cria o banco automaticamente se não existir
)

