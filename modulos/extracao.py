import json
import time
import cv2
from config import *
from google import genai
from utils.persistencia import carregar_listas_pendentes, salvar_listas_pendentes

client = genai.Client(api_key="SUA_CHAVE")

def juntar_imagens_vertical(lista_caminhos_imagens):
    """
    Recebe uma lista de caminhos de imagens (strings)
    e junta todas verticalmente em uma única imagem.

    Exemplo:
    [linha1.jpg, linha2.jpg, linha3.jpg]
    ↓
    vira uma imagem única empilhada verticalmente

    Isso permite enviar tudo em UMA chamada para a IA.
    """

    imagens_cv = []

    # =====================================================
    # 1. CARREGAR TODAS AS IMAGENS
    # =====================================================
    for caminho in lista_caminhos_imagens:
        img = cv2.imread(str(caminho))

        # segurança: evita erro se imagem não carregar
        if img is None:
            continue

        imagens_cv.append(img)

    # =====================================================
    # 2. SE NÃO HOUVER IMAGENS VÁLIDAS
    # =====================================================
    if not imagens_cv:
        return None

    # =====================================================
    # 3. JUNTAR TODAS VERTICALMENTE
    # =====================================================
    imagem_final = cv2.vconcat(imagens_cv)

    return imagem_final

# ============================================================
# 3.3 — FUNÇÃO QUE ENVIA UMA LISTA COMPLETA PARA A IA
# Recebe várias imagens e retorna alunos estruturados
# ============================================================

def extrair_lista_completa(imagens):
    """
    Recebe uma lista de imagens (caminhos)
    e faz UMA chamada para a IA.

    Agora com:
    ✔ controle de tempo entre chamadas
    ✔ controle de limite diário
    """

    print("Quantidade de imagens recebidas para esta lista:", len(imagens))

    imagem_unica = juntar_imagens_vertical(imagens)

    if imagem_unica is None:
        print("❌ Nenhuma imagem válida para envio.")
        return None

    caminho_temp = "temp_envio_ia.jpg"
    cv2.imwrite(caminho_temp, imagem_unica)

    partes = [{"text": prompt}]

    with open(caminho_temp, "rb") as f:
        partes.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": f.read()
            }
        })

    # =====================================================
    # 🔁 CONTROLE DE RETENTATIVA (BACKOFF)
    # =====================================================
    tempos_espera = [120, 240, 480]  # 2min, 4min, 8min

    tentativa = 0

    while tentativa <= len(tempos_espera):

        try:
            print(f"🚀 Tentativa {tentativa + 1}...")

            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=[{"role": "user", "parts": partes}]
            )

            texto = response.text.strip()

            if texto.startswith("```"):
                texto = texto.replace("```json", "").replace("```", "").strip()

            dados = json.loads(texto)

            if not dados:
                raise ValueError("IA retornou JSON vazio.")

            print("✅ Extração bem-sucedida!")
            return dados

        except Exception as e:

            erro_str = str(e)

            # =================================================
            # TRATAR ERRO 503 (RETRY)
            # =================================================
            if "503" in erro_str or "UNAVAILABLE" in erro_str:

                if tentativa < len(tempos_espera):
                    tempo = tempos_espera[tentativa]
                    print(f"⚠️ Erro 503 (alta demanda). Tentando novamente em {tempo//60} min...")
                    time.sleep(tempo)
                    tentativa += 1
                    continue
                else:
                    print("❌ Falhou após várias tentativas (503). Pulando lista.")
                    return "ERRO_503"

            # =================================================
            # OUTROS ERROS (não retry)
            # =================================================
            else:
                print(f"❌ Erro na extração da lista: {e}")
                return None
            
def executar_extracao(listas):
    print("Iniciando extração com IA...")

    #=========================================================
    # LOOP INTELIGENTE
    #=========================================================

    listas_pendentes = carregar_listas_pendentes(
        CAMINHO_PENDENTES,
        listas
    )

    tentativa_global = 1

    while listas_pendentes:

        print(f"\n🔁 CICLO {tentativa_global} - Listas restantes: {len(listas_pendentes)}")

        listas_para_remover = []

        for nome_lista, imagens in listas_pendentes.items():

            print(f"\n📄 Processando: {nome_lista}")

            resultado = extrair_lista_completa(imagens)

            if resultado == "ERRO_503":
                print("🔄 Vai tentar novamente depois...")
                continue

            if resultado is None:
                print("❌ Erro não recuperável. Pulando.")
                listas_para_remover.append(nome_lista)
                continue

            # ✔ sucesso
            caminho_saida = PASTA_JSON / f"{nome_lista}.json"

            with open(caminho_saida, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)

            print("✔ Salvo:", caminho_saida.name)

            listas_para_remover.append(nome_lista)

        # remove listas concluídas
        for nome in listas_para_remover:
            listas_pendentes.pop(nome)

        # 💾 salva estado atual
        salvar_listas_pendentes(listas_pendentes, CAMINHO_PENDENTES)

        tentativa_global += 1

        # espera antes de novo ciclo (evita sobrecarga)
        if listas_pendentes:
            print("\n⏳ Aguardando 2 minutos antes do próximo ciclo...")
            time.sleep(120)

    # espera antes do novo ciclo
    if CAMINHO_PENDENTES.exists():
        CAMINHO_PENDENTES.unlink()
        print("🧹 Arquivo de pendentes removido (tudo concluído)")

    print("Extração finalizada.")