from config import *
import pandas as pd
from pathlib import Path
from datetime import datetime
import json


# ==========================================================
# CARREGAR DADOS
# ==========================================================

def carregar_todos_alunos(PASTA_JSON):

    todos_alunos = []

    for arquivo_json in PASTA_JSON.glob("*.json"):

        with open(arquivo_json, "r", encoding="utf-8") as f:
            dados = json.load(f)

        if dados and "alunos" in dados:
            for aluno in dados["alunos"]:
                aluno["arquivo_origem"] = arquivo_json.name
                todos_alunos.append(aluno)

    print("Total de registros carregados:", len(todos_alunos))

    return todos_alunos


# ==========================================================
# LOG DE VALIDAÇÃO IA
# ==========================================================

def salvar_log_validacoes_ia(erros):

    if not erros:
        return

    df_erros = pd.DataFrame(erros, columns=["linha", "nome", "descricao"])

    df_erros["timestamp_execucao"] = datetime.now().isoformat()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = PASTA_LOGS_VALIDACAO / f"log_validacao_ia_{timestamp}.csv"

    df_erros.to_csv(
        arquivo,
        index=False,
        encoding="utf-8-sig",
        sep=";"
    )

    print("📄 Log de validação IA salvo em:", arquivo)


# ==========================================================
# LOG DE EXECUÇÃO (JSON)
# ==========================================================

def salvar_log_execucao(info_execucao, caminho_logs):

    caminho_logs = Path(PASTA_LOGS_EXECUCAO / "logs_execucao")
    caminho_logs.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"log_execucao_{timestamp}.json"

    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(info_execucao, f, ensure_ascii=False, indent=2)

    print("📊 Log de execução salvo em:", arquivo)


# ==========================================================
# RESUMO
# ==========================================================

def gerar_resumo_execucao(info_execucao):

    resumo = f"""
📊 RESUMO DA EXECUÇÃO

Período: {info_execucao['mes']} de {info_execucao['ano']}

🕒 Início: {info_execucao['inicio_execucao']}
🕒 Fim: {info_execucao['fim_execucao']}

- Registros brutos extraídos: {info_execucao['total_registros_brutos']}
- Registros finais após tratamento: {info_execucao['total_registros_final']}

- Inconsistências detectadas (IA): {info_execucao['total_erros_validacao_ia']}

- Tempo total de execução: {round(info_execucao['tempo_execucao_segundos'], 2)} segundos

Status: {"✅ SUCESSO" if info_execucao['total_erros_validacao_ia'] == 0 else "⚠️ COM ALERTAS"}
"""

    return resumo


# ==========================================================
# SALVAR RESUMO TXT
# ==========================================================

def salvar_resumo_txt(resumo, caminho_logs):

    caminho_logs = Path(PASTA_LOGS_EXECUCAO / "logs_execucao")
    caminho_logs.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"resumo_execucao_{timestamp}.txt"

    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(resumo)

    print("📝 Resumo salvo em:", arquivo)

