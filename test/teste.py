
from pathlib import Path


LOCAL_IMPORT = Path("imports") 


arquivos = [arquivo for arquivo in LOCAL_IMPORT.iterdir() if arquivo.is_file()]
nome_arquivos = list()

if not arquivos:
    raise FileNotFoundError("Nenhum arquivo encontrado na pasta imports")


for arquivo in arquivos:

    nome = arquivo.stem
    formato = arquivo.suffix

    if formato != ".csv":
        raise ValueError(f"Formato de arquivo inválido na pasta imports - {formato}")

    nome_arquivos.append(nome)

print(nome_arquivos)
