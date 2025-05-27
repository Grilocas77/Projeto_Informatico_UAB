# ============================================================
# velvet_runner.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Este módulo é responsável por:
# 🔹 Carregar o modelo de linguagem Velvet (HF)
# 🔹 Gerar respostas traduzidas (PT ➜ EN ➜ PT)
# 🔹 Validar respostas por palavras-chave
# 🔹 Guardar as respostas geradas:
#     - Num ficheiro de histórico (`velvet_respostas.json`)
#     - Num ficheiro temporário com a última resposta (`velvet_ultima_resposta.json`)
# ============================================================

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from config import VELVET_MODEL, HF_TOKEN, VELVET_PARAMS
import json
import os
from pathlib import Path
from models.tradutor_local import traduzir_pt_para_en, traduzir_en_para_pt

# ============================================================
# 🔧 Carregamento do modelo Velvet-2B a partir do HuggingFace
# ============================================================


def load_model():
    # Tokenizer e modelo definidos no config.py
    tokenizer = AutoTokenizer.from_pretrained(VELVET_MODEL, token=HF_TOKEN)
    model = AutoModelForCausalLM.from_pretrained(VELVET_MODEL, token=HF_TOKEN)

    # Cria um pipeline de geração de texto com os parâmetros definidos
    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=0,  # Usa GPU (0) se disponível; CPU (-1) se não
        **VELVET_PARAMS  # Ex: max_new_tokens, temperature, top_k, etc.
    )


# Inicialização do pipeline ao carregar o módulo
model_generator = load_model()

# ============================================================
# 🧠 Geração de resposta traduzida com Velvet
# ============================================================


def generate_response(prompt: str) -> str:
    # Traduz o prompt do utilizador para inglês
    prompt_en = traduzir_pt_para_en(prompt)

    # Gera resposta com Velvet
    generated = model_generator(prompt_en)

    # Extrai o texto gerado
    resposta_en = generated[0]['generated_text']

    # Traduz de volta para português
    resposta_pt = traduzir_en_para_pt(resposta_en)

    # Remove prefixos como "Resposta:" caso existam
    resposta_limpa = resposta_pt.split("Resposta:")[-1].strip()
    return resposta_limpa

# ============================================================
# ✅ Validação de resposta com base em palavras-chave
# ============================================================


def validar_resposta_por_keywords(resposta: str, contexto: str, min_match: int = 3) -> bool:
    """
    Verifica se a resposta contém pelo menos `min_match` palavras com 4+ letras
    em comum com o contexto fornecido.
    """
    import re
    palavras_contexto = re.findall(r'\b\w{4,}\b', contexto.lower())
    palavras_resposta = re.findall(r'\b\w{4,}\b', resposta.lower())
    comuns = set(palavras_contexto).intersection(set(palavras_resposta))
    return len(comuns) >= min_match

# ============================================================
# 💾 Gestão de ficheiros: histórico e última resposta
# ============================================================


# Caminhos dos ficheiros JSON
VELVET_HIST_FILE = Path("data/respostas/velvet_respostas.json")
VELVET_LAST_FILE = Path("data/respostas/velvet_ultima_resposta.json")

# Garante que a pasta 'data/respostas' existe
os.makedirs(VELVET_HIST_FILE.parent, exist_ok=True)


def salvar_completo_em_arquivo(detalhes: dict):
    """
    Guarda os detalhes completos da interação com o modelo.
    Cria dois ficheiros:
    1. Histórico acumulado (JSON com lista)
    2. Última resposta (JSON individual)
    """

    # 1. Carrega ou inicia o histórico
    if VELVET_HIST_FILE.exists():
        with open(VELVET_HIST_FILE, encoding="utf-8") as f:
            historico = json.load(f)
    else:
        historico = []

    # 2. Acrescenta a nova entrada ao histórico
    historico.append(detalhes)

    # 3. Guarda o histórico atualizado
    with open(VELVET_HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

    # 4. Atualiza o ficheiro com a última resposta
    with open(VELVET_LAST_FILE, "w", encoding="utf-8") as f:
        json.dump(detalhes, f, indent=2, ensure_ascii=False)

    # 5. Confirmação no terminal
    print("📝 Resposta guardada em:")
    print(f"   └ Histórico → {VELVET_HIST_FILE}")
    print(f"   └ Última resposta → {VELVET_LAST_FILE}")
