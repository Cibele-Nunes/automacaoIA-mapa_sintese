import json
import shutil
from google import genai
import streamlit as st
from pathlib import Path
from config import *
from modulos.preprocessamento import (
    organizacao_arquivos,
    preprocessar_imagens,
    agrupar_listas,
    limpar_imagens_pos_extracao
)

from modulos.extracao import (
    executar_extracao
)

from modulos.tratamento import (
    carregar_jsons_extraidos,
    executar_tratamento
)

from modulos.preenchimento import (
    executar_preenchimento
)

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

PASTA_CONFIG = Path("config")

ARQUIVO_CONFIG = (
    PASTA_CONFIG / "configuracoes.json"
)

ARQUIVO_LOGO = (
    PASTA_CONFIG / "logo.png"
)

nome_instituicao = NOME_INSTITUICAO_PADRAO

if ARQUIVO_CONFIG.exists():

    with open(
        ARQUIVO_CONFIG,
        "r",
        encoding="utf-8"
    ) as f:

        configuracoes = json.load(f)

    nome_instituicao = configuracoes.get(
        "nome_instituicao",
        NOME_INSTITUICAO_PADRAO
    )

st.set_page_config(
    page_title="Automação do Mapa Síntese",
    layout="wide"
)

st.markdown(
    """
    <h1 style='font-size:40px; margin:2px; padding:5px'>
    📊 Automação do Mapa Síntese
    Versão 1.0.0
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>

    h1 {
    font-size: 3rem !important;
    }

    p {
        font-size: 1.4rem !important;
    }

    div[data-testid="stRadio"] label {
        font-size: 2.1rem !important;
    }

    div[data-testid="stFileUploader"] label {
        font-size: 1.05rem !important;
    }

    button {
        font-size: 1.1rem !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>

    div[role="radiogroup"] label {
        margin-bottom: 15px !important;
        margin-top: 12px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
    )

st.write(
    f"Sistema de processamento automático e elaboração do MAPA SÍNTESE da CPA do {nome_instituicao}."
)

# =========================================================
# MENU
# =========================================================

col1, col2, col3 = st.sidebar.columns([1, 3, 1])

with col2:
    if ARQUIVO_LOGO.exists():

        st.markdown(
            '<div style="text-align: center;">',
            unsafe_allow_html=True
        )

        st.image(
            ARQUIVO_LOGO,
            width=180
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    else:

        st.sidebar.image(
            "assets/logo_padrao.png",
            width=180
        )

st.sidebar.markdown(
    "<h4 style='text-align:center;'>Automação do Mapa Síntese</h4>",
    unsafe_allow_html=True
)

st.sidebar.divider()

modo = st.sidebar.radio(
    "Selecione uma operação:",
    [
        "📂 Processar listas",
        "📊 Preencher Excel",
        "⚙️ Configurações"
    ]
)

st.sidebar.divider()

# =========================================================
# CAMPOS
# =========================================================

if modo != "⚙️ Configurações":
    st.sidebar.write("Selecione o período:")

    ano = st.sidebar.selectbox(
            "Ano",
            ["2026", "2027", "2028", "2029", "2030", 
             "2031", "2032", "2033", "2034", "2035"]
        )

    mes = st.sidebar.selectbox(
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

    mes_exibicao = mes.split("_", 1)[1]

    st.info(
        f"📅 Período selecionado: {mes_exibicao} de {ano}"
    )

st.divider()

uploaded_files = None

if modo == "📂 Processar listas":

    st.header("📂 Processamento de Listas")

    st.info(
        """
        Envie as imagens das listas.

        **O sistema irá:**
        - Pré-processar
        - Extrair com IA
        - Gerar CSV para revisão
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    uploaded_files = st.file_uploader(
        "Imagens das listas selecionadas",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    csv_oficial_upload = None

if modo == "📊 Preencher Excel":

    st.header("📊 Preenchimento do Mapa Síntese")

    st.info(
        """
        Envie o CSV oficial revisado.

        **O sistema irá:**
        - Validar os dados
        - Atualizar o Excel anual
        - Gerar o mapa síntese atualizado
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    csv_oficial_upload = st.file_uploader(
        "CSV Oficial Revisado",
        type=["csv"],
        key="csv_oficial"
    )

if modo == "⚙️ Configurações":

    st.header("⚙️ Configurações do Sistema")

    st.info(
        """
        Configure a identidade visual do sistema.

        Você pode alterar:

        - Nome da instituição
        - Logo da instituição
        - Inteligência Artificial

        """
    )

    nome_escola = st.text_input(
        "Nome da instituição",
        value=nome_instituicao
    )

    logo_upload = st.file_uploader(
        "Escudo da instituição",
        type=["png", "jpg", "jpeg"],
        key="escudo_escola"
    )

    st.subheader(
        "Inteligência Artificial"
    )

    chave_gemini = st.text_input(
        "Chave da API Gemini",
        type="password",
        help="Informe a chave da API utilizada pelo sistema para realizar a extração dos dados."
    )

    if st.button("💾 Salvar Configurações"):

        PASTA_CONFIG.mkdir(
            parents=True,
            exist_ok=True
        )

        configuracoes = {
            "nome_instituicao": nome_escola
        }

        with open(
            ARQUIVO_CONFIG,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                configuracoes,
                f,
                ensure_ascii=False,
                indent=4
            )

        if logo_upload is not None:

            with open(
                ARQUIVO_LOGO,
                "wb"
            ) as f:

                f.write(
                    logo_upload.getbuffer()
                )

        if chave_gemini.strip():

            CAMINHO_API_KEY.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                CAMINHO_API_KEY,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(chave_gemini.strip())

        st.success(
            "✅ Configurações salvas com sucesso!"
        )

    if st.button("🔎 Testar conexão com Gemini"):

        try:

            chave_salva = carregar_api_key()

            cliente_teste = genai.Client(
                api_key=chave_salva
            )

            resposta_teste = cliente_teste.models.generate_content(
                model="gemini-2.5-flash",
                contents="Responda apenas: OK"
            )

            if resposta_teste.text:

                st.success(
                    "✅ Conexão com a API Gemini realizada com sucesso!"
                )

        except FileNotFoundError:

            st.warning(
                "⚠️ A chave da API Gemini ainda não foi configurada. "
                "Informe a chave e clique em 'Salvar Configurações' antes de testar."
            )

        except Exception:

            st.error(
                "❌ Não foi possível conectar à API Gemini. "
                "Verifique se a chave está correta e se a API está disponível."
            )

# =========================================================
# BOTÃO
# =========================================================

if modo != "⚙️ Configurações":
        
    if st.button("Executar"):

        status = st.empty()

        st.subheader("📋 Log de Execução")

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

        if modo == "📂 Processar listas":

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

                # ==========================================================
                # LIMPEZA DAS IMAGENS TEMPORÁRIAS
                # ==========================================================

                status.info("🧹 Limpando imagens temporárias...")

                logs.append("🧹 Limpando imagens temporárias...")

                log_box.code("\n".join(logs))

                limpar_imagens_pos_extracao(
                    lista_imagens,
                    ano,
                    mes
                )

                status.success(
                    "✅ Imagens temporárias removidas."
                )

                logs.append(
                    "✅ Imagens temporárias removidas."
                )

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

                logs.append(f"""
                            📊 RESUMO

                            Período: {mes_exibicao} de {ano}
                            Imagens encontradas: {len(lista_imagens)}
                            Listas agrupadas: {len(listas)}
                            Registros: {len(todos_alunos)}
                            Registros processados: {len(df_final)}
                            Inconsistências: {len(erros)}

                            CSV gerado: {Path(caminho_csv).name}
                            """)
                
                log_box.code(
                    "\n".join(logs)
                )

                logs.append("✅ Processamento concluído")
                
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

        if modo == "📊 Preencher Excel":

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