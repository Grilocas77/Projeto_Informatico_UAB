# ============================================================
# tradutor_local.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# 🔹 Tradução automática local entre Português e Inglês (PT ⇄ EN)
# 🔹 Utiliza modelos MarianMT da HuggingFace, carregados via config.py
# 🔹 Evita dependência de APIs externas, garantindo privacidade e performance
# 🔹 Fornece funções específicas e genéricas para tradução unidirecional e bidirecional
# ============================================================

from config import TRADUTOR_MODELOS


# === Funções de Tradução ===

def traduzir_pt_para_en(texto: str) -> str:
    """
    Traduz uma frase do Português para o Inglês usando modelo MarianMT.

    Args:
        texto (str): Frase ou parágrafo em português.

    Returns:
        str: Tradução em inglês.
    """
    tokenizer = TRADUTOR_MODELOS["pt-en"]["tokenizer"]
    model = TRADUTOR_MODELOS["pt-en"]["model"]
    inputs = tokenizer([texto], return_tensors="pt", padding=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


def traduzir_en_para_pt(texto: str) -> str:
    """
    Traduz uma frase do Inglês para o Português usando modelo MarianMT.

    Args:
        texto (str): Frase ou parágrafo em inglês.

    Returns:
        str: Tradução em português.
    """
    tokenizer = TRADUTOR_MODELOS["en-pt"]["tokenizer"]
    model = TRADUTOR_MODELOS["en-pt"]["model"]
    inputs = tokenizer([texto], return_tensors="pt", padding=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


def traduzir(texto: str, origem: str = "pt", destino: str = "en") -> str:
    """
    Função genérica para traduzir entre Português e Inglês, com autodetecção de direção.

    Args:
        texto (str): Texto a traduzir.
        origem (str): Código do idioma de origem ('pt' ou 'en').
        destino (str): Código do idioma de destino ('pt' ou 'en').

    Returns:
        str: Texto traduzido no idioma desejado.

    Raises:
        ValueError: Se a combinação de idiomas for inválida.
    """
    if origem == "pt" and destino == "en":
        return traduzir_pt_para_en(texto)
    elif origem == "en" and destino == "pt":
        return traduzir_en_para_pt(texto)
    else:
        raise ValueError(f"Tradução não suportada: '{origem}' -> '{destino}'. Use 'pt' ou 'en'.")
