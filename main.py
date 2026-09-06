import argparse

from core.database import db
from core.config import LOCAL_IMPORT
from pony.orm import db_session
from models import *
from scripts import robo
from services.importarCSV import ImportarCSV
import logging



logger = logging.getLogger(__name__)
db.generate_mapping(create_tables=False)



# Argumentos
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


def main():
    args = parse_args()
    logger.info("Iniciando execução do sistema")

    #Rodar bot da ANA (que salvará o arquivo no import), a menos que ja
    #exista um arquivo esperando (import manual) ou o modo manual seja forcado
    if args.manual:
        print("Modo manual: pulando o robo, importando o CSV ja presente na pasta.")
    else:
        try:
            robo.executar()
        except Exception as erro:
            logger.exception("Falha ao executar o robô")

    #Salvar dados
    try:
        ImportarCSV(
            nome_estacao = "Estacao IFSC Cacador", 
            tipo_origem = "WeatherCloud"
        ).executar()

    except Exception as erro:
        logger.exception("Falha ao executar aiImportação do CSV")

    logger.info("Execução do sistema finalizada")


if __name__ == "__main__":
    main()
