from config import *
import pandas as pd
from shutil import copyfile
from openpyxl import load_workbook
from modulos.tratamento import erros_mes

ANO_MES = f"{ANO}_{MES}"
arquivo_oficial = CSV_OFICIAL / f"{ANO_MES}_dataframe_oficial.csv"

if not arquivo_oficial.exists():
    raise FileNotFoundError(f"CSV oficial não encontrado: {arquivo_oficial}")

df_oficial = pd.read_csv(
    arquivo_oficial,
    sep=";",
    encoding="utf-8-sig"
)

print("✔ CSV oficial carregado:", arquivo_oficial.name)
print("Colunas:", df_oficial.columns.tolist())
print("Total de registros:", len(df_oficial))
df_oficial.head()

# Corrigir NOTA
df_oficial["nota"] = (
    df_oficial["nota"]
    .astype(str)
    .str.replace(",", ".", regex=False)
    .str.strip()
)

df_oficial["nota"] = pd.to_numeric(df_oficial["nota"], errors="coerce")

# Corrigir DATA (FORMATO BRASILEIRO)
df_oficial["data"] = pd.to_datetime(
    df_oficial["data"],
    dayfirst=True,
    errors="coerce"
)

# presença
df_oficial["presenca"] = df_oficial["nota"].apply(
    lambda x: "AUSENTE" if pd.isna(x) else "PRESENTE"
)

# resultado oficial
df_oficial["resultado"] = df_oficial.apply(
    lambda r: "REPROVADO" if r["presenca"]=="AUSENTE"
    else ("APROVADO" if r["nota"]>=5 else "REPROVADO"),
    axis=1
)

def remover_registros_invalidos(df):
    df = df.copy()

    # normalizar vazios
    for col in ["area", "etapa", "nota"]:
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col] == "", col] = None
        df.loc[df[col] == "nan", col] = None

    # regra: não possui informação acadêmica nenhuma
    invalido = (
        df["area"].isna() &
        df["etapa"].isna() &
        df["nota"].isna()
    )

    removidos = df[invalido]["nome"].unique()
    df_limpo = df[~invalido]

    print("Registros removidos automaticamente (sem dados acadêmicos):")
    for n in removidos:
        print(" -", n)

    print("\nTotal removido:", len(df) - len(df_limpo))

    return df_limpo

df_oficial = remover_registros_invalidos(df_oficial)

print("Após limpeza:", len(df_oficial))

# verificação automática (ANTI-ERRO HUMANO)
erros = []

# Certifique-se de que 'nota' seja numérico antes das comparações.
df_oficial["nota"] = pd.to_numeric(df_oficial["nota"], errors="coerce")


# 1) Nota em aluno ausente
erro_nota_ausente = df_oficial[
    (df_oficial["presenca"] == "AUSENTE") &
    (df_oficial["nota"].notna())
]
if len(erro_nota_ausente) > 0:
    erros.append(f"Há {len(erro_nota_ausente)} alunos AUSENTES com nota.")

# 2) Resultado inválido
valores_validos = ["APROVADO", "REPROVADO"]
erro_resultado = df_oficial[
    ~df_oficial["resultado"].isin(valores_validos)
]
if len(erro_resultado) > 0:
    erros.append("Existem valores inválidos na coluna RESULTADO.")

# 3) Área vazia
erro_area = df_oficial[
    df_oficial["area"].isna() |
    (df_oficial["area"].astype(str).str.strip() == "")
]
if len(erro_area) > 0:
    erros.append("Existem alunos sem área.")

# 4) Nome vazio
erro_nome = df_oficial[
    df_oficial["nome"].isna() |
    (df_oficial["nome"].astype(str).str.strip() == "")
]
if len(erro_nome) > 0:
    erros.append("Existem alunos sem nome.")

# 5) Nota incompatível com resultado
erro_resultado_nota = df_oficial[
    (df_oficial["nota"] >= 5.0) &
    (df_oficial["resultado"] == "REPROVADO")
]

if len(erro_resultado_nota) > 0:
    erros.append("Existem alunos APROVADOS por nota mas marcados como REPROVADO.")

erro_resultado_nota2 = df_oficial[
    (df_oficial["nota"] < 5.0) &
    (df_oficial["presenca"] == "PRESENTE") &
    (df_oficial["resultado"] == "APROVADO")
]

if len(erro_resultado_nota2) > 0:
    erros.append("Existem alunos com nota abaixo de 5,0 marcados como APROVADO.")

# 6) Nota negativa ou maior que 10
erro_intervalo = df_oficial[
    (df_oficial["nota"] < 0) |
    (df_oficial["nota"] > 10)
]

if len(erro_intervalo) > 0:
    erros.append("Existem notas fora do intervalo 0 a 10.")

# Resultado
if erros:
    print("ERROS ENCONTRADOS:")
    for e in erros:
        print("- ", e)
else:
    print("CSV validado com sucesso — pronto para continuar o pipeline")

print("Total de registros:", len(df_oficial))

# =========================================================
# CARREGAMENTO E ABERTURA DO ARQUIVO ANUAL
# =========================================================

ARQUIVO_ANUAL = PASTA_MAPA_ANUAL / f"MAPA_SINTESE_{ANO}.xlsx"

# Se o arquivo anual ainda não existir, cria a partir do modelo
if not ARQUIVO_ANUAL.exists():
    print("Arquivo anual não encontrado.")
    print("Criando a partir do modelo base...")
    copyfile(ARQUIVO_MODELO, ARQUIVO_ANUAL)
else:
    print("Arquivo anual encontrado. Será atualizado.")

workbook = load_workbook(ARQUIVO_ANUAL)

ws_fundamental = workbook["ENSINO FUNDAMENTAL"]
ws_medio = workbook["ENSINO MÉDIO"]



print(ARQUIVO_ANUAL)
print(ARQUIVO_ANUAL.exists())
print(ARQUIVO_ANUAL.stat().st_size)

if erros and MODO_EXECUCAO == "PRODUCAO":
    print("🚫 MÊS INCOMPLETO — Excel NÃO será gerado")

    for e in erros_mes:
        print("⚠️", e)

else:
    if erros:
        print("⚠️ Mês incompleto, mas permitido em modo AJUSTE")
        for e in erros_mes:
            print("⚠️", e)
    else:
        print("✅ Mês completo")


print(ARQUIVO_MODELO)
print(ARQUIVO_MODELO.exists())

print("Arquivo carregado:")
print(ARQUIVO_MODELO)

print("Sheets disponíveis:")
print(workbook.sheetnames)

df_final = df_oficial.copy()

# padronização FINAL (garantia absoluta antes do Excel)
df_final.columns = df_final.columns.str.lower().str.strip()

df_final["nome"] = df_final["nome"].astype(str).str.strip()
df_final["area"] = df_final["area"].astype(str).str.upper().str.strip()
df_final["etapa"] = df_final["etapa"].astype(str).str.upper().str.strip()
df_final["presenca"] = df_final["presenca"].astype(str).str.upper().str.strip()
df_final["resultado"] = df_final["resultado"].astype(str).str.upper().str.strip()

df_final["nota"] = pd.to_numeric(df_final["nota"], errors="coerce")

print("Dados oficiais carregados para escrita:", len(df_final))
df_final.head()


# ==================================================
# ÁREA ESTRUTURAL DO MODELO (independente da etapa)
# ==================================================

MAPA_ESTRUTURA_EXCEL = {
    "LINGUAGENS E SUAS TECNOLOGIAS": "LINGUAGENS",
    "REDAÇÃO": "REDAÇÃO",
    "CIÊNCIAS HUMANAS": "HISTÓRIA E GEOGRAFIA",
    "MATEMÁTICA E SUAS TECNOLOGIAS": "MATEMÁTICA",
    "CIÊNCIAS DA NATUREZA": "CIÊNCIAS",

    # nomes que já podem vir traduzidos
    "LINGUAGENS": "LINGUAGENS",
    "HUMANAS": "HISTÓRIA E GEOGRAFIA",
    "MATEMÁTICA": "MATEMÁTICA",
    "REDAÇÃO": "REDAÇÃO",
    "REDACAO": "REDAÇÃO",
    "NATUREZA": "CIÊNCIAS",
    "CIÊNCIAS": "CIÊNCIAS"
}


df_final["area_estrutura"] = df_final["area"].map(MAPA_ESTRUTURA_EXCEL)

# validação obrigatória
nao_traduzidas = df_final[df_final["area_estrutura"].isna()][["area"]].drop_duplicates()

if len(nao_traduzidas) > 0:
    print("⚠️ Áreas não reconhecidas:")
    print(nao_traduzidas)
else:
    print("Todas as áreas reconhecidas pelo modelo!")

# ==========================================
# EXTRAIR MÊS DA DATA
# ==========================================

MESES_PT = {
    3:"MARÇO",4:"ABRIL",5:"MAIO",6:"JUNHO",
    7:"JULHO",8:"AGOSTO",9:"SETEMBRO",
    10:"OUTUBRO",11:"NOVEMBRO",12:"DEZEMBRO"
}

df_final["mes"] = df_final["data"].dt.month.map(MESES_PT)

print("Meses encontrados:")
print(df_final["mes"].unique())


# =========================================================
# DIAGNÓSTICO RÁPIDO DE DATA
# =========================================================
print("Tipo da coluna data:", df_oficial["data"].dtype)
print("Mês encontrado:", df_oficial["data"].dt.month.unique())

COLUNAS_TURNO = {
    "VESPERTINO": {
        "INSCRITOS": "H",
        "PRESENTES": "I",
        "AUSENTES": "J",
        "APROVADOS": "K",
        "REPROVADOS": "L"
    },
    "NOTURNO": {
        "INSCRITOS": "M",
        "PRESENTES": "N",
        "AUSENTES": "O",
        "APROVADOS": "P",
        "REPROVADOS": "Q"
    }
}

print("Colunas configuradas dos turnos.")

# ============================================================
# CRIA TABELA RESUMO OFICIAL PARA PREENCHER O MODELO
# ============================================================

df = df_final.copy()

# padronizações de segurança
df["presenca"] = df["presenca"].str.upper().str.strip()
df["resultado"] = df["resultado"].str.upper().str.strip()
df["turno"] = df["turno"].str.upper().str.strip()
df["etapa"] = df["etapa"].str.upper().str.strip()
df["area_estrutura"] = df["area_estrutura"].str.upper().str.strip()
df["mes"] = df["mes"].str.upper().str.strip()

# cria indicadores numéricos
df["inscrito"] = 1
df["presente"] = (df["presenca"] == "PRESENTE").astype(int)
df["ausente"] = (df["presenca"] == "AUSENTE").astype(int)
df["aprovado"] = (df["resultado"] == "APROVADO").astype(int)
df["reprovado"] = (df["resultado"] == "REPROVADO").astype(int)

# agrupamento final
resumo = (
    df.groupby(["etapa","mes","area_estrutura","turno"], as_index=False)
      .agg({
          "inscrito":"sum",
          "presente":"sum",
          "ausente":"sum",
          "aprovado":"sum",
          "reprovado":"sum"
      })
)

# nomes finais (iguais aos do modelo)
resumo = resumo.rename(columns={
    "inscrito":"INSCRITOS",
    "presente":"PRESENTES",
    "ausente":"AUSENTES",
    "aprovado":"APROVADOS",
    "reprovado":"REPROVADOS"
})

print("Resumo criado com sucesso!")
print(resumo.sort_values(["etapa","mes","area_estrutura","turno"]))


# ============================================================
# LOCALIZAÇÃO REAL DAS CÉLULAS NO MODELO (POR COORDENADAS)
# ============================================================

# linha inicial de cada mês
LINHAS_MESES = {
    "MARÇO": 16,
    "ABRIL": 27,
    "MAIO": 38,
    "JUNHO": 49,
    "JULHO": 60,
    "AGOSTO": 71,
    "SETEMBRO": 82,
    "OUTUBRO": 93,
    "NOVEMBRO": 104,
    "DEZEMBRO": 115
}

# distância das áreas em relação ao mês
OFFSET_AREAS = {
    "LINGUAGENS": 3,
    "REDAÇÃO": 4,
    "HISTÓRIA E GEOGRAFIA": 5,
    "MATEMÁTICA": 6,
    "CIÊNCIAS": 7
}


def escrever_no_modelo(ws, etapa_nome):
    """
    Preenche UMA planilha inteira (fundamental ou médio)
    usando a tabela resumo já calculada
    """

    df_etapa = resumo[resumo["etapa"] == etapa_nome]

    for _, linha in df_etapa.iterrows():

        mes = linha["mes"]
        area = linha["area_estrutura"]
        turno = linha["turno"]

        if mes not in LINHAS_MESES:
            print("Mês ignorado:", mes)
            continue

        if area not in OFFSET_AREAS:
            print("Área ignorada:", area)
            continue

        # calcula linha do excel
        linha_excel = LINHAS_MESES[mes] + OFFSET_AREAS[area]

        # escreve cada campo
        for campo in ["INSCRITOS","PRESENTES","AUSENTES","APROVADOS","REPROVADOS"]:

            coluna = COLUNAS_TURNO[turno][campo]
            valor = int(linha[campo])

            ws[f"{coluna}{linha_excel}"] = valor

    print("Planilha preenchida:", etapa_nome)
    print(f"\n🔎 Etapa: {etapa_nome}")
    print("Linhas encontradas:", len(df_etapa))


print(resumo["turno"].unique())

print(sorted(resumo["area_estrutura"].unique()))

print(resumo["mes"].unique())

print(resumo["etapa"].value_counts())

print("Etapas no resumo:")
print(resumo["etapa"].unique())

print("\nTurnos no resumo:")
print(resumo["turno"].unique())

print("\nÁreas no resumo:")
print(sorted(resumo["area_estrutura"].unique()))

print("\nResumo completo:")
print(resumo.head(20))


# ============================================================
# IDENTIFICAR MÊS DO CSV (SISTEMA MÊS A MÊS)
# ============================================================

meses_csv = df_final["mes"].dropna().unique()

if len(meses_csv) != 1:
    raise ValueError(f"CSV deve conter apenas 1 mês. Encontrado: {meses_csv}")

MES_ATUAL = meses_csv[0]

print("Mês detectado no CSV:", MES_ATUAL)

def verificar_mes_preenchido(ws, mes):
    """
    Verifica se o mês já foi preenchido.
    Considera preenchido apenas se a célula
    NÃO contiver mais fórmula (ou seja, já foi escrita).
    """

    if mes not in LINHAS_MESES:
        return False

    linha_base = LINHAS_MESES[mes]

    for offset in OFFSET_AREAS.values():
        linha_excel = linha_base + offset

        for colunas_turno in COLUNAS_TURNO.values():
            for coluna in colunas_turno.values():

                cell = ws[f"{coluna}{linha_excel}"]

                # Se não for fórmula, significa que já foi escrita
                if cell.data_type != "f":
                    if cell.value not in (None, ""):
                        return True

    return False

ja_preenchido_fund = verificar_mes_preenchido(ws_fundamental, MES_ATUAL)
ja_preenchido_medio = verificar_mes_preenchido(ws_medio, MES_ATUAL)

if ja_preenchido_fund or ja_preenchido_medio:
  raise ValueError(
      f"O mês {MES_ATUAL} já possui dados preenchidos no arquivo anual. "
      "Operação bloqueada para evitar sobrescrita."
  )

print("Mês ainda não preenchido. Pode prosseguir.")

# ENSINO FUNDAMENTAL
escrever_no_modelo(ws_fundamental, "ENSINO FUNDAMENTAL")

# ENSINO MÉDIO
escrever_no_modelo(ws_medio, "ENSINO MÉDIO")

print("Planilhas preenchidas com sucesso!")

workbook.save(ARQUIVO_ANUAL)

print("Arquivo anual atualizado com sucesso!")
print("Local:", ARQUIVO_ANUAL)

# ============================================================
# COMANDO UTILIZADO APENAS EM DEZEMBRO APÓS
# PREENCHIMENTO DE TODAS AS TABELAS DAS PLANILHAS
# ============================================================

workbook.save(ARQUIVO_FINAL)

print(ARQUIVO_FINAL, "preenchido com sucesso!")