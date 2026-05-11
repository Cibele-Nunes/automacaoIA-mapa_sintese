from config import *

from modulos.preprocessamento import preprocessar_imagens, agrupar_listas
from modulos.extracao import executar_extracao
from modulos.tratamento import executar_tratamento
from modulos.preenchimento import executar_preenchimento

from utils.logs import carregar_todos_alunos


def main():
    
    print("\n=== AUTOMAÇÃO MAPA SÍNTESE ===\n")

    print("1 - Processar listas e gerar CSV revisão")
    print("2 - Preencher Excel com CSV oficial")

    opcao = input("\nEscolha uma opção: ").strip()
    if opcao == 1:

        print("\n🚀 INICIANDO PROCESSAMENTO COMPLETO\n")

        # ==========================================================
        # 1. PRÉ-PROCESSAMENTO
        # ==========================================================
        print("📷 Pré-processamento das imagens...")

        lista_imagens = list(PASTA_IMAGENS.glob("*"))

        imagens_processadas = preprocessar_imagens(
            lista_imagens
        )

        # ==========================================================
        # 2. AGRUPAMENTO DAS LISTAS
        # ==========================================================
        print("\n📑 Agrupando listas...")

        listas = agrupar_listas(imagens_processadas)

        print(f"Total de listas encontradas: {len(listas)}")

        # ==========================================================
        # 3. EXTRAÇÃO COM IA
        # ==========================================================
        print("\n🤖 Extração com IA...")

        executar_extracao(listas)

        # ==========================================================
        # 4. TRATAMENTO DOS DADOS
        # ==========================================================
        print("\n📊 Tratamento dos dados...")

        todos_alunos = carregar_todos_alunos(PASTA_JSON_EXTRAIDO)

        df_final, erros, erros_mes, caminho_csv = executar_tratamento(
            todos_alunos,
            ANO,
            MES,
            PASTA_RESULTADOS
        )

        print("\nCSV para revisão gerado em:")
        print(caminho_csv)

    elif opcao == "2":

        # ==========================================================
        # 5. PREENCHIMENTO DO EXCEL
        # ==========================================================
        print("\n📘 Preenchendo o mapa síntese...")

        executar_preenchimento(ANO, MES)

        print("\n✅ PROCESSO FINALIZADO COM SUCESSO!\n")

# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    main()