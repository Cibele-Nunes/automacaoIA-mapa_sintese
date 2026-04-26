import cv2
import os
import re
from config import *
import numpy as np
from datetime import datetime
from collections import defaultdict
from pathlib import Path

#=========================================================
# ORGANIZAÇÃO DE ARQUIVOS — LEITURA DIRETA DO DRIVE
#=========================================================
# Garante que a pasta existe
# Lista somente imagens válidas
# Evita rodar pipeline vazio
# Não usa mais upload manual
# Funciona para qualquer funcionário

def organizacao_arquivos(lista_imagens):

    print("Selecionando período para processamento...")

    if not os.path.exists(PASTA_IMAGENS):
        raise FileNotFoundError(f"Pasta não encontrada: {PASTA_IMAGENS}")

    lista_imagens = [
        os.path.join(PASTA_IMAGENS, f)
        for f in os.listdir(PASTA_IMAGENS)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    print("Ano selecionado:", ANO)
    print("Mês selecionado:", MES)
    print("Total de imagens encontradas:", len(lista_imagens))

    if not lista_imagens:
        raise ValueError("Nenhuma imagem encontrada. Verifique a pasta.")
    else:
        print("Imagens prontas para processamento.")

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def extrair_data(nome_arquivo):
    match = re.search(r'\d{4}-\d{2}-\d{2}', nome_arquivo)
    if match:
        return match.group(0)
    return None

def eh_dia_linguagens(data_str):
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
        dia_semana = data.weekday()

        # segunda-feira = 0
        return dia_semana == 0

    except:
        return False

def detectar_linhas_horizontais(imagem):
    # binarização leve
    _, binaria = cv2.threshold(imagem, 180, 255, cv2.THRESH_BINARY_INV)

    # kernel horizontal
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))

    linhas = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel)

    return linhas

def encontrar_linha_de_corte(imagem, nome_arquivo):
    linhas = detectar_linhas_horizontais(imagem)

    cv2.imwrite(f"debug_{nome_arquivo}.jpg", linhas)

    altura = linhas.shape[0]

    # soma de pixels por linha
    soma_linhas = np.sum(linhas, axis=1)

    # região central da imagem
    inicio = int(altura * 0.3)
    fim = int(altura * 0.7)

    # procura linha com MENOS pixels (espaço vazio)
    corte = inicio + np.argmin(soma_linhas[inicio:fim])

    return corte

def segmentar_linhas_alunos(imagem, nome_arquivo="debug"):

    altura, largura = imagem.shape

    # =====================================================
    # 1. BINARIZAÇÃO (destaca texto)
    # =====================================================
    _, binaria = cv2.threshold(imagem, 150, 255, cv2.THRESH_BINARY_INV)

    # =====================================================
    # 2. DILATAÇÃO (junta textos da mesma linha)
    # =====================================================
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 5))
    dilatada = cv2.dilate(binaria, kernel, iterations=1)

    # DEBUG opcional
    # cv2.imwrite(f"debug_dilatada_{nome_arquivo}.jpg", dilatada)

    # =====================================================
    # 3. PROJEÇÃO VERTICAL (soma por linha)
    # =====================================================
    soma_linhas = np.sum(dilatada, axis=1)

    # =====================================================
    # 4. DETECTAR REGIÕES COM CONTEÚDO
    # =====================================================
    limiar = np.max(soma_linhas) * 0.1

    regioes = []
    dentro = False
    inicio = 0

    for i, valor in enumerate(soma_linhas):
        if valor > limiar and not dentro:
            inicio = i
            dentro = True
        elif valor <= limiar and dentro:
            fim = i
            dentro = False
            regioes.append((inicio, fim))

    # caso termine dentro
    if dentro:
        regioes.append((inicio, altura))

    # =====================================================
    # 5. GERAR IMAGENS DAS LINHAS
    # =====================================================
    imagens_linhas = []

    for (y1, y2) in regioes:

        altura_linha = y2 - y1

        if altura_linha < 15:
            continue

        linha_img = imagem[y1:y2, :]

        imagens_linhas.append(linha_img)

    return imagens_linhas

# =========================================================
# FUNÇÃO PRINCIPAL DE PRÉ-PROCESSAMENTO
# =========================================================

def preprocessar_e_dividir(caminho_entrada, pasta_saida):

    imagem = cv2.imread(caminho_entrada)
    nome_arquivo = os.path.basename(caminho_entrada)

    data = extrair_data(nome_arquivo)

    print(f"Data: {data} | Linguagens? {eh_dia_linguagens(data)}")

    # =====================================================
    # PRÉ-PROCESSAMENTO BÁSICO
    # =====================================================
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    imagem_contraste = clahe.apply(imagem_cinza)

    imagem_suave = cv2.GaussianBlur(imagem_contraste, (3, 3), 0)

    altura, largura = imagem_suave.shape

    # corta margens laterais
    imagem_processada = imagem_suave[:, int(largura*0.05):int(largura*0.95)]

    imagens_saida = []

    nome_base = os.path.splitext(nome_arquivo)[0]

    # =====================================================
    # CASO 1 — LINGUAGENS (PRECISA CORTAR)
    # =====================================================
    if eh_dia_linguagens(data):

        corte = encontrar_linha_de_corte(imagem_processada, nome_arquivo)

        margem = 10

        parte1 = imagem_processada[:corte - margem, :]
        parte2 = imagem_processada[corte + margem:, :]

        # =================================================
        # SEGMENTAÇÃO APENAS DAS PARTES
        # =================================================
        linhas_parte1 = segmentar_linhas_alunos(parte1, nome_base + "_p1")
        linhas_parte2 = segmentar_linhas_alunos(parte2, nome_base + "_p2")

        # salvar parte 1
        for i, linha in enumerate(linhas_parte1):
            caminho = os.path.join(pasta_saida, f"{nome_base}_p1_linha_{i}.jpg")
            cv2.imwrite(caminho, linha)
            imagens_saida.append(caminho)

        # salvar parte 2
        for i, linha in enumerate(linhas_parte2):
            caminho = os.path.join(pasta_saida, f"{nome_base}_p2_linha_{i}.jpg")
            cv2.imwrite(caminho, linha)
            imagens_saida.append(caminho)

        print("✂️ Cortada e segmentada:", nome_arquivo)

    # =====================================================
    # CASO 2 — OUTROS DIAS
    # =====================================================
    else:

        linhas = segmentar_linhas_alunos(imagem_processada, nome_base)

        for i, linha in enumerate(linhas):
            caminho = os.path.join(pasta_saida, f"{nome_base}_linha_{i}.jpg")
            cv2.imwrite(caminho, linha)
            imagens_saida.append(caminho)

        print("🖼️ Segmentada:", nome_arquivo)

    return imagens_saida

# =========================================================
# EXECUÇÃO
# =========================================================

def preprocessar_imagens(lista_imagens, pasta_saida):
    print("Iniciando pré-processamento...")

    lista_processadas = []

    for caminho_origem in sorted(lista_imagens):

        nome_base = Path(caminho_origem).stem

        arquivos_existentes = list(pasta_saida.glob(f"{nome_base}*"))

        if arquivos_existentes:
            print(f"⏭️ Já processado: {nome_base}")
            continue

        novas = preprocessar_e_dividir(
            caminho_origem,
            pasta_saida
        )

        lista_processadas.extend(novas)

    print("Total de imagens finais:", len(lista_processadas))
    print("Pré-processamento finalizado.")

    return lista_processadas

def agrupar_listas(imagens_processadas):
    """
    Agrupa imagens por lista.

    Ex:
    noturno_2025-07-14_p1_linha_1.jpg
    noturno_2025-07-14_p1_linha_2.jpg

    → vira um grupo: noturno_2025-07-14
    """

    listas = defaultdict(list)

    for img in sorted(imagens_processadas):
        nome = Path(img).stem.lower()

        # pega turno + data
        chave_lista = "_".join(nome.split("_")[:2])

        listas[chave_lista].append(img)

    return listas