# Log - início

from config import *
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# Ler todos os JSON gerados pela IA
todos_alunos = []

# percorre todos os arquivos json gerados
for arquivo_json in PASTA_JSON.glob("*.json"):

    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if dados is None:
        continue

    # adiciona metadados do arquivo (origem da lista)
    if "alunos" in dados:
        for aluno in dados["alunos"]:
            aluno["arquivo_origem"] = arquivo_json.name
            todos_alunos.append(aluno)

print("Total de registros carregados:", len(todos_alunos))

inicio_execucao = datetime.now()
timestamp_execucao = inicio_execucao.isoformat()

total_brutos = len(todos_alunos)
total_jsons = len(list(PASTA_JSON.glob("*.json")))

LOGS_VALIDACAO = Path(PASTA_PROCESSADAS, "logs_validacao")
LOGS_VALIDACAO.mkdir(parents=True, exist_ok=True)

def salvar_log_validacoes_ia(erros, caminho):
    
    if not erros:
        return

    df_erros = pd.DataFrame(erros, columns=["linha", "nome", "descricao"])

    df_erros["timestamp_execucao"] = datetime.now().isoformat()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = LOGS_VALIDACAO / f"log_validacao_ia_{timestamp}.csv"

    df_erros.to_csv(
        arquivo,
        index=False,
        encoding="utf-8-sig",
        sep=";"
    )

    print("📄 Log de validação IA salvo em:", arquivo)

def salvar_log_execucao(info_execucao, pasta_logs):
    pasta_logs = Path(pasta_logs)
    pasta_logs.mkdir(parents=True, exist_ok=True)

    caminho_log = pasta_logs / "log_execucao.csv"

    df_novo = pd.DataFrame([info_execucao])

    if caminho_log.exists():
        df_existente = pd.read_csv(caminho_log)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    df_final.to_csv(caminho_log, index=False, encoding="utf-8-sig", sep=";")

    print("Log de execução atualizado em:", caminho_log)

# Funções do log de execução

def gerar_resumo_execucao(info_execucao):
    resumo = f"""
📊 RESUMO DA EXECUÇÃO

Período: {info_execucao['mes']} de {info_execucao['ano']}

🕒 Início: {info_execucao['inicio_execucao']}
🕒 Fim: {info_execucao['fim_execucao']}

- Listas processadas: {info_execucao['total_arquivos_json']}
- Registros brutos extraídos: {info_execucao['total_registros_brutos']}
- Registros finais após tratamento: {info_execucao['total_registros_final']}

- Inconsistências detectadas (IA): {info_execucao['total_erros_validacao_ia']}

- Tempo total de execução: {round(info_execucao['tempo_execucao_segundos'], 2)} segundos

Status: {"✅ SUCESSO" if info_execucao['total_erros_validacao_ia'] == 0 else "⚠️ COM ALERTAS"}

"""
    return resumo


def salvar_resumo_txt(resumo, caminho_logs):
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"resumo_execucao_{timestamp}.txt"

    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(resumo)

    print("📝 Resumo salvo em:", arquivo)

def salvar_log_execucao(info_execucao, caminho_logs):
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"log_execucao_{timestamp}.json"

    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(info_execucao, f, ensure_ascii=False, indent=2)

    print("📊 Log de execução salvo em:", arquivo)

def salvar_resumo_txt(resumo, caminho_logs):
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"resumo_execucao_{timestamp}.txt"

    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(resumo)

    print("📝 Resumo salvo em:", arquivo)

def salvar_log_execucao(info_execucao, caminho_logs):
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = caminho_logs / f"log_execucao_{timestamp}.json"

    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(info_execucao, f, ensure_ascii=False, indent=2)

    print("📊 Log de execução salvo em:", arquivo)


