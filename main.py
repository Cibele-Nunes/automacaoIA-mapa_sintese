from config import *
from modulos.preprocessamento import preprocessar_imagens, agrupar_listas
from modulos.extracao import executar_extracao
from modulos.tratamento import executar_tratamento

def main():
    print("🚀 Iniciando sistema...")

    # 1. carregar imagens
    lista_imagens = list(PASTA_ENTRADA.glob("*.jpg"))

    # 2. preprocessamento
    imagens_processadas = preprocessar_imagens(
        lista_imagens,
        PASTA_PROCESSADAS
    )

    # 3. agrupamento (você já tem essa função)
    listas = agrupar_listas(imagens_processadas)

    # 4. extração
    executar_extracao(listas)

    print("✅ Processo finalizado")

if __name__ == "__main__":
    main()