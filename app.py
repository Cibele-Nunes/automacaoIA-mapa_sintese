import streamlit as st
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
    layout="centered"
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

# =========================================================
# BOTÃO
# =========================================================

if st.button("Executar"):

    st.info("Iniciando operação...")

    if modo == "Processar listas":

        try:

            st.write("📂 Lendo imagens...")

            lista_imagens = organizacao_arquivos(ano, mes)

            st.write(
                f"✅ {len(lista_imagens)} imagens encontradas."
            )

            st.write("🖼️ Iniciando pré-processamento...")

            imagens_processadas = preprocessar_imagens(lista_imagens, ano, mes)

            st.success(
                f"✅ Pré-processamento concluído.\n"
                f"{len(imagens_processadas)} imagens geradas."
            )

            st.write("📚 Agrupando listas...")

            listas = agrupar_listas(imagens_processadas)

            st.write("📚 Listas agrupadas:")

            for nome_lista, imagens in listas.items():
                  
                  st.write(f"📄 {nome_lista} → "        
                           f"{len(imagens)} imagens"
                    )

            st.success(f"✅ {len(listas)} listas agrupadas.")

            st.write("🤖 Iniciando extração IA...")

            executar_extracao(listas, ano, mes)

            st.success("✅ Extração finalizada.")

            st.write("📥 Carregando JSONs extraídos...")

            todos_alunos = carregar_jsons_extraidos(ano, mes)

            st.success(f"✅ {len(todos_alunos)} registros carregados.")

            st.write("🧹 Iniciando tratamento dos dados...")

            df_final, erros, erros_mes, caminho_csv = (
                 executar_tratamento(todos_alunos, ano, mes, PASTA_RESULTADOS))
            
            st.success("✅ Tratamento concluído.")

            st.write("📄 CSV gerado:")
            st.write(str(caminho_csv))

        except Exception as e:

            st.error(f"❌ Erro:\n{e}")

    if modo == "Preencher Excel":

        try:

            st.write("📄 Iniciando preenchimento do Excel...")

            executar_preenchimento(ano, mes)

            st.success("✅ Preenchimento concluído com sucesso!")

        except Exception as e:

            st.error(f"❌ Erro:\n{e}")