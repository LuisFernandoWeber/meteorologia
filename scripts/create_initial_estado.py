from app.core.database import db
from app.services.estado.create_estado import create_estado

try:
    db.generate_mapping(create_tables=True)

    create_estado("Santa Catarina", "SC")
    create_estado("Rio Grande do Sul", "RS")
    create_estado("Parana", "PR")

    print("Dados inseridos na tabela Estados com sucesso!")

except Exception as e:
    print(f"Ocorreu um erro ao inserir os dados em Estados. Erro: {e}")
