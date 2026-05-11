import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.logs import *

def normalizar_area(area):
    if not area:
        return area

    area = area.upper().strip()

    if "LINGUAGENS" in area:
        return "LINGUAGENS"
    elif "HUMANAS" in area:
        return "HUMANAS"
    elif "MATEM" in area:
        return "MATEMÁTICA"
    elif "NATUREZA" in area:
        return "NATUREZA"
    elif "REDA" in area:
        return "REDAÇÃO"

    return area

def normalizar_etapa(etapa):
    """
    Padroniza a etapa para:
    - ENSINO FUNDAMENTAL
    - ENSINO MÉDIO
    """

    if not etapa:
        return etapa

    etapa = str(etapa).upper().strip()

    # remove espaços duplicados
    etapa = " ".join(etapa.split())

    # ===============================
    # FUNDAMENTAL
    # ===============================
    if "FUND" in etapa:
        return "ENSINO FUNDAMENTAL"

    # ===============================
    # MÉDIO (com ou sem acento)
    # ===============================
    if "MED" in etapa or "MÉD" in etapa:
        return "ENSINO MÉDIO"

    # ===============================
    # fallback (caso estranho)
    # ===============================
    return etapa

def pipeline_tratamento(todos_alunos):
    # ==========================================================
    # 1) Criação do DataFrame base
    # ==========================================================
    df = pd.DataFrame(todos_alunos)

    # =========================================================
    # NORMALIZAR ÁREA (ANTES DA VALIDAÇÃO)
    # =========================================================
    df["area"] = df["area"].apply(normalizar_area)

    # Garante que todas as colunas existam (evita KeyError)
    colunas_esperadas = [
        "nome", "area", "etapa", "nota",
        "presenca", "resultado", "arquivo_origem"
    ]
    for col in colunas_esperadas:
        if col not in df.columns:
            df[col] = None

    # ==========================================================
    # 2) Extração de TURNO e DATA do nome do arquivo
    # Formato esperado: vespertino_2025-08-13_01.json
    # ==========================================================
    def extrair_data_turno(nome_arquivo):
        """
        Extrai TURNO e DATA do nome do arquivo no formato:
        vespertino_2025-08-13_01.json
        noturno_2025-08-14_02.json
        """

        try:
          data_match = re.search(r'\d{4}-\d{2}-\d{2}', nome_arquivo)
          data = data_match.group(0) if data_match else None
          if "noturno" in nome_arquivo.lower():
            turno = "noturno"
          elif "vespertino" in nome_arquivo.lower():
            turno = "vespertino"
          else:
            turno = "desconhecido"

          return data, turno

        except:
          return None, "erro"

    # ==========================================================
    # 2.1) Aplicar extração ao DataFrame
    # cria colunas data e turno a partir do nome do arquivo
    df[["data","turno"]] = df["arquivo_origem"].apply(
        lambda x: pd.Series(extrair_data_turno(x))
    )

    # garante que existam mesmo se não encontrar nada
    if "data" not in df.columns:
        df["data"] = None
    if "turno" not in df.columns:
        df["turno"] = None

    # ==========================================================
    # 3) Padronização de texto
    # ==========================================================
    def limpar_texto(col):
        return (
            col.astype(str)
               .str.upper()
               .str.strip()
               .str.replace(r"\s+", " ", regex=True)
        )

    df["nome"] = limpar_texto(df["nome"])
    df["area"] = limpar_texto(df["area"])
    df["etapa"] = limpar_texto(df["etapa"])
    df["etapa"] = df["etapa"].apply(normalizar_etapa)
    df["resultado"] = limpar_texto(df["resultado"])
    df["presenca"] = limpar_texto(df["presenca"])

    # ==========================================================
    # 4) Presença
    # Nota numérica (única fonte confiável)
    # ==========================================================
    df["nota"] = pd.to_numeric(df["nota"], errors="coerce")

    # ==========================================================
    # 5) Presença (regra oficial do colégio)
    # AUSENTE -> sem número
    # PRESENTE -> possui número
    # ==========================================================
    df["presenca"] = df["nota"].apply(
    lambda x: "AUSENTE" if pd.isna(x) else "PRESENTE"
    )

    # ==========================================================
    # 6) Resultado (regra oficial)
    # ==========================================================
    def calcular_resultado(row):
      if row["presenca"] == "AUSENTE":
        return "REPROVADO"
      if row["nota"] >= 5.0:
        return "APROVADO"
      return "REPROVADO"

    df["resultado"] = "REPROVADO"
    df.loc[(df["presenca"] == "PRESENTE") & (df["nota"] >= 5.0), "resultado"] = "APROVADO"

    # ==========================================================
    # 7) Criação da chave única do aluno na prova
    # ==========================================================
    df["chave_unica"] = (
        df["nome"].fillna("") + "|" +
        df["data"].fillna("") + "|" +
        df["area"].fillna("")
    )

    # ==========================================================
    # 8) Remoção de duplicados
    # ==========================================================
    df = df.drop_duplicates(subset="chave_unica", keep="first").copy()

    # ==========================================================
    # 9) Ordenação final para conferência humana
    # ==========================================================
    df = df.sort_values(["data", "turno", "area", "nome"]).reset_index(drop=True)

    return df

def validar_dados(df):

    df_erros = pd.DataFrame()

    # ===============================
    # Nota x Presença inconsistente
    # ===============================
    erro1 = df[
        ((df["nota"].isna()) & (df["presenca"] == "PRESENTE")) |
        ((df["nota"].notna()) & (df["presenca"] == "AUSENTE"))
    ].copy()

    if not erro1.empty:
        erro1["tipo_erro"] = "NOTA_PRESENCA_INCONSISTENTE"
        df_erros = pd.concat([df_erros, erro1])

    # ===============================
    # Resultado inconsistente
    # ===============================
    erro2 = df[
        (df["nota"].notna()) &
        (
            ((df["nota"] >= 5.0) & (df["resultado"] != "APROVADO")) |
            ((df["nota"] < 5.0) & (df["resultado"] != "REPROVADO"))
        )
    ].copy()

    if not erro2.empty:
        erro2["tipo_erro"] = "RESULTADO_INCONSISTENTE"
        df_erros = pd.concat([df_erros, erro2])

    # ===============================
    # Nome suspeito (assinatura)
    # ===============================
    erro3 = df[df["nome"].str.split().str.len() <= 2].copy()

    if not erro3.empty:
        erro3["tipo_erro"] = "NOME_SUSPEITO_ASSINATURA"
        df_erros = pd.concat([df_erros, erro3])

    # ===============================
    # Etapa inválida
    # ===============================
    erro4 = df[~df["etapa"].isin(["ENSINO FUNDAMENTAL", "ENSINO MÉDIO"])].copy()

    if not erro4.empty:
        erro4["tipo_erro"] = "ETAPA_INVALIDA"
        df_erros = pd.concat([df_erros, erro4])

    # ===============================
    # Salvar relatório se houver erro
    # ===============================
    if not df_erros.empty:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_log = PASTA_LOGS_VALIDACAO / f"log_validacao_{timestamp}.csv"

        df_erros["timestamp_execucao"] = datetime.now().isoformat()

        df_erros.to_csv(
            caminho_log,
            index=False,
            encoding="utf-8-sig",
            sep=";"
        )

        print("Foram encontradas inconsistências.")
        print("Relatório salvo em:", caminho_log)

    else:
        print("Nenhuma inconsistência encontrada.")

    return df

def validar_inconsistencias(df):
    erros = []

    for i, row in df.iterrows():
        nome = row["nome"]
        area = row["area"]
        nota = row["nota"]
        presenca = row["presenca"]
        resultado = row["resultado"]

        # Regra 1: presença x nota
        if pd.isna(nota) and presenca == "PRESENTE":
            erros.append((i, nome, "Presença inconsistente com nota"))

        if not pd.isna(nota) and presenca == "AUSENTE":
            erros.append((i, nome, "Ausente com nota preenchida"))

        # Regra 2: resultado x nota
        try:
            nota_float = float(nota)
            if nota_float >= 5 and resultado != "APROVADO":
                erros.append((i, nome, "Resultado incorreto"))
            if nota_float < 5 and resultado != "REPROVADO":
                erros.append((i, nome, "Resultado incorreto"))
        except:
            pass

        # Regra 3: área inválida
        areas_validas = [
            "LINGUAGENS",
            "REDAÇÃO",
            "HUMANAS",
            "MATEMÁTICA",
            "NATUREZA"
        ]
        if area not in areas_validas:
          erros.append((i, nome, "Área suspeita"))

    return erros

def validar_areas_duplicadas(df):
    erros = []

    duplicados = df[df.duplicated("nome", keep=False)]

    for nome, grupo in duplicados.groupby("nome"):
        areas = grupo["area"].unique()

        # Se só tem uma área, mas deveria ter duas → suspeito
        if len(areas) == 1:
            erros.append((nome, "Possível erro: duplicado com mesma área"))

    return erros

def validar_linguagens_redacao(df):
    erros = []

    duplicados = df[df.duplicated(["nome", "data"], keep=False)]

    for (nome, data), grupo in duplicados.groupby(["nome", "data"]):

        areas = grupo["area"].tolist()

        if any("LINGUAGENS" in a for a in areas) and any("REDAÇÃO" in a for a in areas):

            notas = grupo["nota"].tolist()

            # se uma nota é NaN e outra não → suspeito
            if any(pd.isna(n) for n in notas) and any(not pd.isna(n) for n in notas):
                erros.append((nome, data, "Possível troca entre Linguagens e Redação"))

    return erros

def validar_notas_suspeitas(df):
    erros = []

    duplicados = df[df.duplicated("nome", keep=False)]

    for nome, grupo in duplicados.groupby("nome"):
        if len(grupo) == 2:
            notas = grupo["nota"].values

            # Ex: uma tem nota e outra "-"
            if "-" in notas and any(n != "-" for n in notas):
                erros.append((nome, "Possível troca de nota entre áreas"))

    return erros

def executar_validacoes(df):
    erros = []

    erros += validar_inconsistencias(df)
    erros += validar_areas_duplicadas(df)
    erros += validar_notas_suspeitas(df)
    erros += validar_linguagens_redacao(df)

    if erros:
        print(f"⚠️ {len(erros)} inconsistências encontradas")
        print("Dados precisam de revisão antes do Excel")

        for e in erros[:10]:
            print(e)

        salvar_log_validacoes_ia(erros)

    else:
        print("✅ Nenhuma inconsistência crítica encontrada")

    return erros

def salvar_csv_revisao(df, pasta_resultados, ano, mes):

    pasta = Path(pasta_resultados) / "csv_revisao"
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / f"{ano}_{mes}_dataframe_final.csv"

    df.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
        sep=";"
    )

    print("📄 CSV gerado:", caminho)

    return caminho

def validar_mes_completo(df, mes):
    problemas = []

    dias = sorted(df["data"].dropna().unique())
    total_dias = len(dias)

    # regra por mês (baseado no calendário real)
    DIAS_ESPERADOS = {
        "01_JANEIRO": 8,
        "02_FEVEREIRO": 8,
        "03_MARÇO": 8,
        "04_ABRIL": 8,
        "05_MAIO": 8,
        "06_JUNHO": 4,
        "07_JULHO": 4,
        "08_AGOSTO": 8,
        "09_SETEMBRO": 8,
        "10_OUTUBRO": 8,
        "11_NOVEMBRO": 8,
        "12_DEZEMBRO": 4
    }

    esperado = DIAS_ESPERADOS.get(mes, 8)

    if total_dias < esperado:
        problemas.append(f"Dias insuficientes: {total_dias}/{esperado}")

    # valida Linguagens + Redação no mesmo dia
    for dia in dias:
        areas_dia = df[df["data"] == dia]["area"].unique()

        tem_linguagens = any("LINGUAGENS" in a for a in areas_dia)
        tem_redacao = any("REDAÇÃO" in a for a in areas_dia)

        if tem_linguagens and not tem_redacao:
            problemas.append(f"{dia}: Linguagens sem Redação")

        if tem_redacao and not tem_linguagens:
            problemas.append(f"{dia}: Redação sem Linguagens")

    return problemas

def executar_tratamento(todos_alunos, ano, mes, pasta_resultados):

    inicio_execucao = datetime.now()

    total_brutos = len(todos_alunos)

    df = pipeline_tratamento(todos_alunos)
    df = validar_dados(df)

    erros = executar_validacoes(df)
    erros_mes = validar_mes_completo(df, mes)

    total_final = len(df)
    total_erros = len(erros)

    print("Total de linhas finais:", total_final)

    caminho_csv = salvar_csv_revisao(df, pasta_resultados, ano, mes)

    fim_execucao = datetime.now()
    tempo_execucao = (fim_execucao - inicio_execucao).total_seconds()

    info_execucao = {
        "ano": ano,
        "mes": mes,
        "total_registros_brutos": total_brutos,
        "total_registros_final": total_final,
        "total_erros_validacao_ia": total_erros,
        "tempo_execucao_segundos": tempo_execucao,
        "inicio_execucao": inicio_execucao.isoformat(),
        "fim_execucao": fim_execucao.isoformat(),
        "status": "SUCESSO" if total_erros == 0 else "COM_ALERTAS"
    }

    salvar_log_execucao(info_execucao, PASTA_LOGS_EXECUCAO)

    resumo = gerar_resumo_execucao(info_execucao)
    print(resumo)
    salvar_resumo_txt(resumo, PASTA_LOGS_EXECUCAO)

    return df, erros, erros_mes, caminho_csv




