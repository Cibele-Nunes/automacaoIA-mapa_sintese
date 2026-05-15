from pathlib import Path
from config import *

def validar_api_key():

    if not CAMINHO_API_KEY.exists():
        raise FileNotFoundError(
            f"Arquivo da API não encontrado:\n{CAMINHO_API_KEY}"
        )

    chave = carregar_api_key()

    if not chave.strip():
        raise ValueError("Arquivo da API está vazio.")

    print("✅ API key validada.")
