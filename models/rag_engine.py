# ============================================================
# rag_engine.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# 🔹 Recupera contexto vetorial Chroma, rerank com CrossEncoder,
# 🔹 Limita por tokens, remove ruído como títulos, figuras, números, refs.
# ============================================================

from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder
import unicodedata
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import AutoTokenizer
from config import CHROMA_PATH, EMBEDDING_MODEL, K_SIMILARITY_SEARCH, MAX_PROMPT_TOKENS
from models.tradutor_local import traduzir
import re

# === Inicialização de embeddings, tokenizer e reranker ===
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def get_chroma_db():
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

def normalize_text(text: str, max_length: int = 1000) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    return text[:max_length].replace("\n", " ")

def limpar_ruido_contexto(texto: str) -> str:
    linhas = texto.splitlines()
    filtradas = []
    for linha in linhas:
        l = linha.strip()
        if len(l) < 30:
            continue
        # Ruído: títulos/caps lock, figura, refs numéricas, tabelas, datas, enumerações, notas de rodapé, marcadores de página, etc.
        if (
            re.match(r"^[A-Z0-9 \-–\.:]{10,}$", l)      # títulos em maiúsculas ou blocos
            or re.match(r"^([0-9]+\.){2,}", l)          # enumeração tipo "7.3.1" ou "1.2.3.4"
            or re.search(r"\bfig(ura)?[\. ]", l, re.I)  # figuras
            or re.search(r"^\[\d+\]|\d{4}$", l)         # refs tipo [1], [23], datas "2023"
            or re.search(r"^Tabela\s*\d+", l, re.I)     # tabelas
            or re.match(r"^\s*\d+\s*$", l)              # números sozinhos
            or re.search(r"(FONTE|EXERC[ÍI]CIO|ANEXO|CAP[ÍI]TULO|INTRODUÇÃO|SUMÁRIO|ÍNDICE|PÁGINA)", l, re.I)
        ):
            continue
        filtradas.append(l)
    texto_limpo = " ".join(filtradas)
    return re.sub(r"\s{2,}", " ", texto_limpo).strip()

def truncate_by_tokens(text: str, max_tokens: int, tok) -> str:
    tokens = tok.encode(text, add_special_tokens=False)
    if len(tokens) <= max_tokens:
        return text
    truncated_tokens = tokens[:max_tokens]
    return tok.decode(truncated_tokens)

def is_generic_context(context: str) -> bool:
    # Heurística: demasiado curto, só exemplos, ruído, ou ausência de frases declarativas
    if len(context) < 100:
        return True
    if re.search(r"figura|exemplo|veja|observe|nota|referência", context, re.I):
        return True
    return False

def retrieve_context(query: str, k: int = K_SIMILARITY_SEARCH, max_candidates: int = 20, return_scores: bool = False, return_raw: bool = False):
    debug_ctx = {}
    debug_ctx["context_en"] = ""

    try:
        query_en = traduzir(query, origem="pt", destino="en")
        debug_ctx["query_en"] = query_en
    except Exception as erro_tq:
        print("❌ Erro ao traduzir a query:", erro_tq)
        query_en = query
        debug_ctx["query_en"] = query_en

    chroma_db = get_chroma_db()
    context_docs = chroma_db.similarity_search(query_en, k=max_candidates)

    if not context_docs:
        contexto_vazio = "Sem contexto relevante encontrado."
        if return_scores and return_raw:
            return contexto_vazio, [], "", "", debug_ctx
        elif return_scores:
            return contexto_vazio, []
        else:
            return contexto_vazio

    # Rerank CrossEncoder
    pairs = [(query_en, doc.page_content) for doc in context_docs]
    scores = reranker.predict(pairs)
    reranked = sorted(zip(context_docs, scores), key=lambda x: x[1], reverse=True)
    TOP_N = 12

    selected_chunks = []
    token_count = 0
    seen_texts = set()

    for doc, score in reranked:
        chunk_text = doc.page_content
        chunk_tokens = len(tokenizer.encode(chunk_text, add_special_tokens=False))
        if any(chunk_text in s or s in chunk_text for s in seen_texts):
            continue

        # Heurística anti-ruído (descarta chunk se for detetado ruído)
        chunk_clean = limpar_ruido_contexto(chunk_text)
        # Se ficou demasiado curto após limpeza, ignora
        if len(chunk_clean) < 100:
            continue

        if token_count + chunk_tokens > MAX_PROMPT_TOKENS:
            break

        selected_chunks.append(chunk_clean)
        token_count += chunk_tokens
        seen_texts.add(chunk_text)

    # Junta todos os chunks relevantes até ao máximo de tokens
    context_pt = "\n\n".join(selected_chunks)
    context_pt_truncado = truncate_by_tokens(context_pt, MAX_PROMPT_TOKENS, tokenizer)
    debug_ctx["context_pt"] = context_pt_truncado

    # Heurística genérica de contexto fraco
    if is_generic_context(context_pt_truncado):
        print("⚠️ O contexto recuperado é genérico ou contém ruído.")

    # Traduzir para EN
    try:
        context_en = traduzir(context_pt_truncado, origem="pt", destino="en")
        context_en = truncate_by_tokens(context_en, MAX_PROMPT_TOKENS, tokenizer)
        debug_ctx["context_en"] = context_en
    except Exception as erro_ctx:
        print("⚠️ Erro ao traduzir o contexto para EN:", erro_ctx)
        context_en = context_pt_truncado[:500]
        debug_ctx["context_en"] = context_en

    texto_limpo = limpar_ruido_contexto(context_pt_truncado)
    texto_normalizado = normalize_text(texto_limpo[:800])
    debug_ctx["normalizado"] = texto_normalizado

    if return_scores and return_raw:
        return context_pt_truncado, reranked, context_en, texto_normalizado, debug_ctx
    elif return_scores:
        return context_pt_truncado, reranked
    else:
        return context_pt_truncado

# 🧪 Teste direto (não faz build/update!)
if __name__ == "__main__":
    db = get_chroma_db()
    print("🔁 Teste de busca:", db.similarity_search("Teste de contexto", k=1))
