# ============================================================
# chatbot_engine.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# 🔹 Carregar modelo de embeddings (SentenceTransformer) para busca semântica
# 🔹 Aceder à base ChromaDB com documentos embebidos
# 🔹 Realizar busca heurística com similaridade vetorial
# 🔹 Identificar o melhor documento com base em similaridade de cosseno
# 🔹 Suporte para retorno direto ou impressão da melhor resposta
# ============================================================

from sentence_transformers import SentenceTransformer, util
from models.rag_engine import get_chroma_db
from config import EMBEDDING_MODEL, TOP_K_SEARCH, MAX_DOC_CHARS
from controllers.logger import log_evento


def busca_local_heuristica(
    pergunta: str,
    k: int = TOP_K_SEARCH,
    retorna: bool = False
) -> str:
    """
    Realiza busca semântica local com embeddings e ChromaDB.
    Args:
        pergunta (str): Pergunta do utilizador (em português ou inglês).
        k (int): Número de documentos a recuperar (_top-k_).
        retorna (bool): Se True, retorna _string_ da melhor resposta, senão imprime.
    Returns:
        str: Melhor resposta encontrada ou mensagem padrão.
    Observações:
        - Suporta lista de dicts ou lista de tuplas (dict, ...).
        - Limita resposta a MAX_DOC_CHARS carateres.
        - Todos os eventos relevantes são registados via logger.
    """
    log_evento(f"🔍 Pergunta recebida: {pergunta}")

    # Carrega modelo de embeddings definido em config
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Acede à base local de embeddings via ChromaDB
    collection = get_chroma_db()
    resultados = collection.similarity_search(query=pergunta, k=k)

    if not resultados:
        log_evento("Nenhum resultado encontrado na busca semântica.")
        return "Desculpe, não encontrei informações relevantes."

    # Normaliza resultados (lista de dicts ou lista de tuplas)
    if isinstance(resultados[0], tuple):
        melhores_docs = [d[0]['page_content'] for d in resultados if isinstance(d, tuple) and len(d) > 0 and 'page_content' in d[0]]
    else:
        melhores_docs = [d['page_content'] for d in resultados if 'page_content' in d]

    if not melhores_docs:
        log_evento("Resultados encontrados mas sem texto válido em 'page_content'.")
        return "Desculpe, não encontrei informações relevantes."

    # Encontra o melhor documento por similaridade de cosseno
    emb_pergunta = model.encode(pergunta, convert_to_tensor=True)
    melhor_doc = max(
        melhores_docs,
        key=lambda d: util.pytorch_cos_sim(emb_pergunta, model.encode([d], convert_to_tensor=True)).mean().item()
    )

    melhor_doc = melhor_doc[:MAX_DOC_CHARS]
    log_evento(f"Melhor resposta selecionada (primeiros 100 chars): {melhor_doc[:100]}...")

    if retorna:
        return melhor_doc

    print(f"\n✅ Melhor resposta:\n{melhor_doc}")
