import cv2
import os
import re
import numpy as np
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from config import *


# ==========================================================
# ORGANIZAÇÃO DE ARQUIVOS
# ==========================================================
# Garante que a pasta existe
# Lista somente imagens válidas
# Evita rodar pipeline vazio
# Não usa mais upload manual
# Funciona para qualquer funcionário

def organizacao_arquivos():
    """
    Lê imagens da pasta e valida entrada
    """

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
        raise ValueError("Nenhuma imagem encontrada.")
    
    print("Imagens prontas para processamento.")

    return lista_imagens


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def extrair_data(nome_arquivo):
    match = re.search(r'\d{4}-\d{2}-\d{2}', nome_arquivo)
    return match.group(0) if match else None


def eh_dia_linguagens(data_str):
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
        return data.weekday() == 0  # segunda-feira
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
        if (y2 - y1) < 15:
            continue

        linha_img = imagem[y1:y2, :]
        imagens_linhas.append(linha_img)

    return imagens_linhas

# ==========================================================
# FUNÇÃO PRINCIPAL - PROCESSAMENTO DE UMA IMAGEM
# ==========================================================

def preprocessar_e_dividir(caminho_entrada, pasta_saida):
    imagem = cv2.imread(caminho_entrada)

    if imagem is None:
        print(f"❌ Erro ao carregar: {caminho_entrada}")
        return []

    nome_arquivo = os.path.basename(caminho_entrada)
    nome_base = os.path.splitext(nome_arquivo)[0]

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
        linhas_p1 = segmentar_linhas_alunos(parte1, nome_base + "_p1")
        linhas_p2 = segmentar_linhas_alunos(parte2, nome_base + "_p2")

        # salvar parte 1
        for i, linha in enumerate(linhas_p1):
            caminho = os.path.join(pasta_saida, f"{nome_base}_p1_linha_{i}.jpg")
            cv2.imwrite(caminho, linha)
            imagens_saida.append(caminho)

        # salvar parte 2
        for i, linha in enumerate(linhas_p2):
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


# ==========================================================
# EXECUÇÃO - LOOP PRINCIPAL
# ==========================================================

def preprocessar_imagens(lista_imagens, pasta_saida):
    print("Iniciando pré-processamento...")

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

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


# ==========================================================
# AGRUPAMENTO
# ==========================================================

def agrupar_listas(imagens_processadas):

    listas = defaultdict(list)

    for img in sorted(imagens_processadas):
        nome = Path(img).stem.lower()
        chave = "_".join(nome.split("_")[:2])
        listas[chave].append(img)

    return listas