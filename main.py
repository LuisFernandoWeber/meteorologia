import argparse

from core.database import db
from core.config import LOCAL_IMPORT
from pony.orm import db_session
from models import *
from scripts import robo
from services.importarCSV import ImportarCSV

db.generate_mapping(create_tables=False)


"""
    Importar tabelas Estacão Caçador
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Importacao de dados da Estacao IFSC Cacador"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help=(
            "Forca o modo manual: pula a execucao do robo mesmo que a "
            "pasta de import esteja vazia."
        ),
    )
    return parser.parse_args()


def existe_arquivo_para_importar():
    """Verifica se ja existe algum arquivo esperando na pasta de import
    (colocado manualmente ou deixado por uma execucao anterior)."""
    return any(arquivo.is_file() for arquivo in LOCAL_IMPORT.iterdir())


def main():
    args = parse_args()

    #Rodar bot da ANA (que salvará o arquivo no import), a menos que ja
    #exista um arquivo esperando (import manual) ou o modo manual seja forcado
    if args.manual:
        print("Modo manual: pulando o robo, importando o CSV ja presente na pasta.")
    elif existe_arquivo_para_importar():
        print("Ja existe um arquivo na pasta de import: pulando o robo.")
    else:
        try:
            robo.executar()
        except Exception as erro:
            print(f"ERRO ao executar o robo: {erro}")

    #Salvar dados
    try:
        ImportarCSV(nome_estacao="Estacao IFSC Cacador").executar()
    except Exception as erro:
        print(f"ERRO: {erro}")

    print("Sistema rodado com sucesso")


if __name__ == "__main__":
    main()