from pathlib import Path

# ===============================
# BASE DO PROJETO
# ===============================
BASE_DIR = Path(__file__).parent

# ===============================
# CONFIG GERAIS
# ===============================
ANO = "2025"
MES = "09_SETEMBRO"
MODO_EXECUCAO = "AJUSTE"
# NODO_EXECUCAO pode ser "AJUSTE" ou "PRODUCAO"
# "AJUSTE" → permite rodar mesmo incompleto
# "PRODUCAO" → bloqueia Excel se incompleto
# ===============================
# PASTAS
# ===============================
PASTA_DADOS = BASE_DIR / "dados"

PASTA_ENTRADA = PASTA_DADOS / "entrada"
PASTA_PROCESSADAS = PASTA_DADOS / "processadas"
PASTA_JSON = PASTA_DADOS / "json"
PASTA_RESULTADOS = PASTA_DADOS / "resultados"
PASTA_SISTEMA = PASTA_DADOS / "sistema"

# subpastas
PASTA_IMAGENS = Path(PASTA_ENTRADA, ANO, MES)
PASTA_IMAGENS_PROCESSADAS = Path(PASTA_PROCESSADAS, "imagens_processadas")
PASTA_JSON_EXTRAIDO = Path(PASTA_JSON, ANO, MES)
PASTA_LOGS_IA = PASTA_PROCESSADAS, "pasta_logs"
PASTA_LOGS_EXECUCAO = PASTA_RESULTADOS / "logs_execucao"
PASTA_LOGS_EXECUCAO.mkdir(parents=True, exist_ok=True)
PASTA_MAPA_ANUAL = PASTA_RESULTADOS / "mapa_sintese_anual"
PASTA_MAPA_ANUAL.mkdir(parents=True, exist_ok=True)
CSV_OFICIAL = Path(PASTA_PROCESSADAS, "csv_revisado")
ARQUIVO_MODELO = Path(PASTA_SISTEMA, "modelo_base", "modelo.xlsx")
ARQUIVO_FINAL_TEMPLATE = (PASTA_RESULTADOS / "arquivo_final"/ "SALVADOR - ROBERTO SANTOS - MAPA SINTESE POR UC MARÇO A DEZEMBRO {ano}.xlsx")

# cria automaticamente se não existir
for pasta in [
    PASTA_ENTRADA,
    PASTA_PROCESSADAS,
    PASTA_JSON,
    PASTA_RESULTADOS,
    PASTA_SISTEMA
]:
    pasta.mkdir(parents=True, exist_ok=True)

CAMINHO_API_KEY = Path(PASTA_SISTEMA, "sistema_interno", "chave_gemini.txt")

def carregar_api_key():
    if not CAMINHO_API_KEY.exists():
        raise FileNotFoundError("Arquivo da API key não encontrado.")

    with open(CAMINHO_API_KEY, "r", encoding="utf-8") as f:
        return f.read().strip()

# ===============================
# ARQUIVO DE PENDENTES
# ===============================
CAMINHO_PENDENTES = PASTA_JSON / "listas_pendentes.json"
LOGS_VALIDACAO = PASTA_PROCESSADAS / "logs_validacao"
LOGS_EXECUCAO = PASTA_LOGS_EXECUCAO / "logs_execucao"


prompt = """
Você é um extrator de dados de alta precisão, sua tarefa é analisar imagens que contêm tabelas com listas oficiais de presença de alunos.
Você deve ler as linhas dessas tabelas e organizar os dados em um formato JSON estruturado.
Extraia estritamente os campos: nome, area, etapa e nota. Ignore as demais colunas presentes na imagem.

As imagens podem conter:
- Uma ou mais páginas da MESMA lista
- Repetição do cabeçalho da tabela
- Assinaturas de professores
- Dados manuscritos adicionados ao final da lista
- A coluna Nota possui os valores manuscritos
- Um mesmo aluno pode aparecer em múltiplas linhas se estiver inscrito em áreas diferentes (ex: uma linha para 'LINGUAGENS E SUAS TECNOLOGIAS' e outra para 'REDAÇÃO'). Você deve gerar um objeto JSON independente para cada uma dessas linhas.

========================================
REGRAS DE FIDELIDADE AOS DADOS
========================================
Sua função é transcrever a tabela exatamente como ela aparece, sem qualquer interpretação. Siga estas diretrizes rigorosamente:
1.	Fidelidade Absoluta: Atue apenas como um extrator. Se um nome estiver incompleto, uma nota estiver faltando ou houver um erro evidente na tabela, transcreva o erro ou a ausência exatamente como está.
2.	Proibição de Inferências: Não tente adivinhar nomes, áreas ou notas baseando-se no contexto ou em linhas anteriores.
3.	Integridade dos Registros: Nunca mude a área de um aluno ou redistribua notas. Cada linha deve ser tratada como um dado isolado e imutável.
4.	Dados Ausentes: Se uma célula estiver em branco, use null ou "" (string vazia) no JSON. Nunca invente valores para "completar" o objeto.
5.	Sem Reorganização: Mantenha a ordem dos dados conforme aparecem visualmente na imagem.

========================================
ALERTA CRÍTICO: PROCESSAMENTO DE ÁREAS DUPLAS
========================================
As áreas “LINGUAGENS E SUAS TECNOLOGIAS” e “REDAÇÃO” aparecem na mesma lista.
•	Listas com duas áreas: Trate cada área como listas diferentes. Será lista de “LINGUAGENS E SUAS TECNOLOGIAS” e lista de “REDAÇÃO”.
•	Duplicidade Esperada: É comum encontrar o mesmo aluno em duas linhas consecutivas: uma para "LINGUAGENS E SUAS TECNOLOGIAS" e outra para "REDAÇÃO".
•	Independência de Notas: As notas de "LINGUAGENS E SUAS TECNOLOGIAS" e "REDAÇÃO" são independentes. É terminantemente proibido copiar a nota de uma linha para a outra.
•	Isolamento de Linha: Processe cada linha de forma independente. Ignore o conteúdo das linhas adjacentes ao extrair os valores de uma célula.
•	Conferência Visual: Transcreva apenas o valor numérico que está fisicamente alinhado à área correspondente na imagem.
Ignore as colunas de CPF, E-mail, PNE e Assinatura. Extraia apenas os outros 4 campos abaixo, Nome, Área, Etapa e Nota, seguindo este formato para cada linha da imagem:
Dados na Imagem (Exemplo):
CPF	Nome	E-mail	Área	Etapa	PNE	Nota	Assinatura
123...	MARIA SOUZA	maria@...	LINGUAGENS E SUAS TECNOLOGIAS	Médio	Não	7,5	(Assinado)
123...	MARIA SOUZA	maria@...	REDAÇÃO	Médio	Não	9,0	(Assinado)
JSON Resultante (Obrigatório):
[
  {
    "nome": "MARIA SOUZA",
    "area": "LINGUAGENS E SUAS TECNOLOGIAS",
    "etapa": "MÉDIO",
    "nota": 7.5
  },
  {
    "nome": "MARIA SOUZA",
    "area": "REDAÇÃO",
    "etapa": "MÉDIO",
    "nota": 9.0
  }
]

========================================
REGRA CRÍTICA DE ALINHAMENTO VISUAL
========================================

Você deve considerar que cada linha da tabela é definida por alinhamento horizontal.

Antes de extrair os dados:

1. Identifique visualmente as linhas horizontais da tabela.
2. Para cada linha:
   - O nome, a área, a etapa e a nota devem estar na MESMA LINHA HORIZONTAL.
3. Nunca associe uma nota que esteja em uma linha diferente do nome.
4. Nunca associe uma área que esteja em uma linha diferente do nome.
5. Se houver dúvida sobre alinhamento:
   - DESCARTE a linha
   - NÃO tente corrigir

CRÍTICO:
A coluna "Área" está localizada aproximadamente no centro horizontal da tabela.
Ao extrair a área, considere apenas o texto alinhado horizontalmente com o nome na mesma linha.
NUNCA utilize áreas de linhas acima ou abaixo.
NUNCA inferir área com base em repetição de padrão.

========================================
COMPORTAMENTO DE EXTRAÇÃO - REFINAMENTO DO PASSO A PASSO
========================================
Para cada linha detectada na tabela:
1.	Identifique a ÁREA: Localize a área em cada linha horizontal.
2.	Se houver mais de uma ÁREA: Separe os dados de cada uma, nome, etapa e nota.
3.	Identifique o NOME: Localize o nome do aluno no início da linha.
4.	Identifique a ETAPA: Localize se é FUNDAMENTAL ou MÉDIO. Importante: Leia o valor escrito na linha atual; não repita o valor da linha de cima ou de baixo automaticamente.
5.	Identifique a NOTA: Localize o valor numérico manuscrito na coluna NOTA. Este valor deve estar na mesma linha do NOME e ETAPA identificados nos passos anteriores. Ignore as colunas que ficam entre elas.
6.	Crie o arquivo JSON: Extraia Nome, Área, Etapa e Nota de cada linha e armazene em formato json.

========================================
REGRAS CRÍTICAS DE LINHA (ALTAMENTE PRIORITÁRIO)
========================================
1. Cada linha da tabela representa UM REGISTRO INDEPENDENTE.
   NUNCA misture informações entre linhas.
2. A coluna "Área" define EXCLUSIVAMENTE a área daquele registro da coluna Nome.
   NÃO inferir.
   NÃO copiar de outra linha.
   NÃO assumir padrão.
   NUNCA troque a área, a etapa ou a nota de um nome.
3. As áreas "LINGUAGENS E SUAS TECNOLOGIAS" e "REDAÇÃO"
   aparecem na MESMA tabela, mas são TOTALMENTE INDEPENDENTES.
   NUNCA misturar registros de "LINGUAGENS E SUAS TECNOLOGIAS"
   com registros de "REDAÇÃO" e vice-versa
4. Se um mesmo nome aparecer mais de uma vez:
   - Trate cada ocorrência como um registro diferente
   - Cada um com sua própria área, nota e presença
5. É PROIBIDO:
   - Copiar área de outra linha
   - Copiar nota de outra linha
   - Misturar dados entre alunos
   - Reutilizar valores de outra linha
   - Trocar a área, etapa ou nota de um nome da mesma linha
6. A extração deve ser feita estritamente linha por linha,
   respeitando alinhamento horizontal da tabela.
7. Se houver dúvida em uma linha:
   - NÃO use outras linhas para decidir
   - Extraia apenas o que estiver visível nela

========================================
REGRAS ESTRUTURAIS
========================================
1. Extraia SOMENTE linhas que estejam claramente dentro da grade da tabela principal.
2. Ignore completamente:
   - Assinaturas e rubricas
   - Nomes isolados no rodapé
   - Textos fora da grade da tabela
- Cabeçalhos repetidos
3. O reaparecimento do cabeçalho NÃO indica nova lista
4. Alunos Manuscritos: Extraia apenas se houver Nome, Área, Etapa e Nota escritos. NUNCA crie um nome, área, etapa ou nota. Alunos manuscritos só devem ser extraídos se estiverem estruturados com: nome + área + etapa + nota.

========================================
REGRAS DE NOTA E RESULTADO
========================================
1. Se houver valor numérico na coluna NOTA:
   → presenca = PRESENTE
2. Se houver "-", vazio ou marca não numérica:
   → presenca = AUSENTE
3. Média de aprovação = 5.0:
   - Nota >= 5.0 → APROVADO
   - Nota < 5.0 → REPROVADO
4. Se AUSENTE → resultado = REPROVADO
5. Se nota = SR → tratar como 0.0 → REPROVADO
6. Se nota ilegível, mas visivelmente numérica:
   → resultado = "NOTA_ILEGIVEL"
7. Nunca inventar nota
8. Nunca modificar etapa

========================================
RESTRIÇÕES ESTRITAS (PARA EVITAR ALUCINAÇÃO)
========================================
- NÃO propague dados verticalmente. Se a coluna "Etapa" estiver vazia em uma linha, mas preenchida na de cima, mantenha vazia ou extraia o que está lá.
- NÃO assuma que porque o aluno está em "Linguagens" ele também está em "Redação" (verifique sempre a coluna Área).
- Ignore cabeçalhos repetidos e assinaturas no rodapé.
- Manuscritos: Extraia apenas se houver Nome, Área, Etapa e Nota mínimos.

========================================
FORMATO DE SAÍDA (JSON PURO)
========================================
{
  "alunos": [
    {
      "nome": "NOME COMPLETO",
      "area": "ÁREA EXATA DA LISTA",
      "etapa": "ENSINO FUNDAMENTAL ou ENSINO MÉDIO",
      "nota": "VALOR",
      "presenca": "PRESENTE/AUSENTE",
      "resultado": "APROVADO/REPROVADO"
    }
  ]
}
"""

# ===============================
# VARIÁVEIS DO PREENCHIMENTO
# ===============================

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

MESES_PT = {
    3:"MARÇO",4:"ABRIL",5:"MAIO",6:"JUNHO",
    7:"JULHO",8:"AGOSTO",9:"SETEMBRO",
    10:"OUTUBRO",11:"NOVEMBRO",12:"DEZEMBRO"
}

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