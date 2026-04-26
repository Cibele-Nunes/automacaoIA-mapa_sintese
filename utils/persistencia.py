import json
from pathlib import Path

# =====================================================
# FUNÇÕES DE PERSISTÊNCIA
# =====================================================

def salvar_listas_pendentes(listas_pendentes, caminho):
    
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(list(listas_pendentes.keys()), f, indent=2)

    print(f"💾 Listas pendentes salvas: {len(listas_pendentes)}")


def carregar_listas_pendentes(caminho, listas_originais):
    
    if not Path(caminho).exists():
        return listas_originais  # começa normal

    with open(caminho, "r", encoding="utf-8") as f:
        nomes = json.load(f)

    listas_filtradas = {
        nome: listas_originais[nome]
        for nome in nomes if nome in listas_originais
    }

    print(f"🔁 Retomando {len(listas_filtradas)} listas pendentes")

    return listas_filtradas