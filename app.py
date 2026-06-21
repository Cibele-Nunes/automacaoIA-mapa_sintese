import streamlit as st
from pathlib import Path
from config import *
from modulos.preprocessamento import (
    organizacao_arquivos,
    preprocessar_imagens,
    agrupar_listas
)

from modulos.extracao import (
    executar_extracao
)

from modulos.tratamento import (
    carregar_jsons_extraidos,
    executar_tratamento
)

from config import PASTA_RESULTADOS
from modulos.preenchimento import (
    executar_preenchimento
)

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Automação Mapa Síntese",
    layout="wide"
)

# =========================================================
# TÍTULO
# =========================================================

st.title("📊 Automação Mapa Síntese")

st.write(
    """
Sistema de processamento automático das listas
do Colégio Estadual Roberto Santos.
"""
)

# =========================================================
# MENU
# =========================================================

modo = st.radio(
    "Selecione uma operação:",
    [
        "Processar listas",
        "Preencher Excel"
    ]
)

# =========================================================
# CAMPOS
# =========================================================

ano = st.selectbox(
    "Ano",
    ["2026", 
     "2025"]
)

mes = st.selectbox(
    "Mês",
    [
        "03_MARÇO",
        "04_ABRIL",
        "05_MAIO",
        "06_JUNHO",
        "07_JULHO",
        "08_AGOSTO",
        "09_SETEMBRO",
        "10_OUTUBRO",
        "11_NOVEMBRO",
        "12_DEZEMBRO"
    ]
)

uploaded_files = None

if modo == "Processar listas":

    uploaded_files = st.file_uploader(
        "Imagens das listas selecionadas",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

csv_oficial_upload = None

if modo == "Preencher Excel":

    csv_oficial_upload = st.file_uploader(
        "CSV Oficial Revisado",
        type=["csv"],
        key="csv_oficial"
    )

# =========================================================
# BOTÃO
# =========================================================

if st.button("Executar"):

    status = st.empty()

    log_box = st.empty()

    logs = []

    if uploaded_files:

        pasta_entrada = (
            PASTA_ENTRADA
            / ano
            / mes
        )

        pasta_entrada.mkdir(
            parents=True,
            exist_ok=True
        )

        arquivos_novos = 0
        arquivos_ignorados = 0

        for arquivo in uploaded_files:

            destino = (
                pasta_entrada
                / arquivo.name
            )

            if destino.exists():
                arquivos_ignorados += 1
                continue

            with open(destino, "wb") as f:
                f.write(arquivo.getbuffer())

            arquivos_novos += 1

        logs.append(
            f"📤 {arquivos_novos} imagens enviadas."
        )

        if arquivos_ignorados > 0:

            logs.append(
                f"⏭️ {arquivos_ignorados} imagens já existiam e foram ignoradas."
            )

        log_box.code(
            "\n".join(logs)
        )

    status.info("🚀 Iniciando operação...")

    if modo == "Processar listas":

        try:

            status.info("📂 Lendo imagens...")

            logs.append("📂 Lendo imagens...")
            
            log_box.code("\n".join(logs))

            lista_imagens = organizacao_arquivos(ano, mes)

            logs.append(f"✅ {len(lista_imagens)} imagens encontradas.")

            log_box.code("\n".join(logs))

            mes_exibicao = mes.split("_", 1)[1]

            logs.append(f"📅 Período em processamento: {mes_exibicao} de {ano}")

            log_box.code("\n".join(logs))

            status.info("🖼️ Iniciando pré-processamento...")

            logs.append("🖼️ Iniciando pré-processamento...")
            
            log_box.code("\n".join(logs))

            barra_preprocessamento = st.progress(0)

            imagens_processadas = preprocessar_imagens(lista_imagens, ano, mes, barra_preprocessamento)

            logs.append(f"{len(imagens_processadas)} imagens geradas.")
            
            log_box.code("\n".join(logs))
            
            status.success(
                f"{len(imagens_processadas)} imagens geradas.\n"
                f"✅ Pré-processamento concluído."
            )

            logs.append(f"✅ Pré-processamento concluído.\n")
            
            log_box.code("\n".join(logs))

            status.info("📚 Agrupando imagens de cada lista...")

            logs.append("📚 Agrupando imagens de cada lista...")
            
            log_box.code("\n".join(logs))

            listas = agrupar_listas(imagens_processadas)

            status.info("📚 Listas agrupadas:")

            for nome_lista, imagens in listas.items():
                  
                  status.info(f"📄 {nome_lista} → "        
                           f"{len(imagens)} imagens"
                    )

            status.success(f"✅ Total de grupos formados {len(listas)}.")

            logs.append(f"✅ Total de grupos formados {len(listas)}.")
            
            log_box.code("\n".join(logs))

            status.info("🤖 Iniciando extração IA...")

            logs.append("🤖 Iniciando extração IA...")
            
            log_box.code("\n".join(logs))

            barra_extracao = st.progress(0)

            executar_extracao(listas, ano, mes, barra_extracao)

            status.success("✅ Extração finalizada.")

            logs.append("✅ Extração finalizada.")
            
            log_box.code("\n".join(logs))

            status.info("📥 Carregando JSONs extraídos...")

            todos_alunos = carregar_jsons_extraidos(ano, mes)

            status.success(f"✅ {len(todos_alunos)} registros carregados.")

            logs.append(f"✅ {len(todos_alunos)} registros encontrados.")
            
            log_box.code("\n".join(logs))

            status.info("🧹 Iniciando tratamento dos dados...")

            logs.append("🧹 Iniciando tratamento dos dados...")
            
            log_box.code("\n".join(logs))
        
            df_final, erros, erros_mes, caminho_csv = (
                 executar_tratamento(todos_alunos, ano, mes, PASTA_RESULTADOS))
            
            status.success("✅ Tratamento concluído.")

            logs.append("✅ Tratamento concluído.")
            
            log_box.code("\n".join(logs))

            status.info("📄 CSV gerado:")
            status.info(str(caminho_csv))

            logs.append(f"📄 CSV gerado com sucesso em: {str(caminho_csv)}")
            
            log_box.code("\n".join(logs))

            with open(caminho_csv, "rb") as arquivo:
                
                st.download_button(
                    label="📥 Baixar CSV de Revisão",
                    data=arquivo,
                    file_name=Path(caminho_csv).name,
                    mime="text/csv"
                )

        except Exception as e:

            status.error(f"❌ Erro:\n{e}")

    if modo == "Preencher Excel":

        try:

            status.info("📄 Iniciando preenchimento do Excel...")

            logs.append("📄 Iniciando preenchimento do Excel...")
            
            log_box.code("\n".join(logs))

            if csv_oficial_upload is None:
                 
                 st.error(
                      "Selecione o CSV oficial revisado."
                )
                 st.stop()

            caminho_csv = (CSV_OFICIAL / f"{ano}_{mes}_dataframe_oficial.csv")

            with open(caminho_csv, "wb") as f:
                 
                 f.write(csv_oficial_upload.getbuffer())

            logs.append("📄 CSV oficial enviado.")

            log_box.code(
                "\n".join(logs)
            )

            caminho_excel = executar_preenchimento(ano, mes)

            status.success("✅ Preenchimento concluído com sucesso!")

            logs.append("✅ Preenchimento concluído com sucesso!")
            
            log_box.code("\n".join(logs))

            with open(caminho_excel, "rb") as arquivo:
                st.download_button(
                    label="📥 Baixar Mapa Síntese Atualizado",
                    data=arquivo,
                    file_name=Path(caminho_excel).name,
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    )
                )

            status.success("✅ Operação concluída!")

            logs.append("✅ Operação concluída!")
            
            log_box.code("\n".join(logs))

        except Exception as e:

            status.error(f"❌ Erro:\n{e}")