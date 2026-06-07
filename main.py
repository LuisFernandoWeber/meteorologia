from core.database import db
import models

try:
    db.generate_mapping(create_tables=True)
    print("Tabelas criadas com sucesso!")
except Exception as e:
    print(f"Erro ao criar as Tabelas. Erro: {e}")


print("Sistema inicializado")
