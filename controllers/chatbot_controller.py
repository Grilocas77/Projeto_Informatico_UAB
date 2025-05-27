# ============================================================
# chatbot_controller.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Este módulo é responsável por:
# 🔹 Coordenar o ciclo completo de interação com o utilizador
# 🔹 Integrar os módulos de:
#     - Recuperação de contexto (RAG com ChromaDB)
#     - Tradução bidirecional (PT ➜ EN ➜ PT)
#     - Geração de resposta com Velvet-2B
#     - Validação automática por palavras-chave
# 🔹 Exibir métricas de resposta (tokens, tempo, validação)
# 🔹 Guardar a interação completa:
#     - Em histórico (velvet_respostas.json)
#     - Em ficheiro temporário com a última resposta (velvet_ultima_resposta.json)
#     - Em ficheiro de métricas (velvet_metrics.jsonl)
#     - Em ficheiro de logs técnicos (velvet_logs.txt)
# ============================================================

import time
import re
from models.velvet_runner import generate_response, salvar_completo_em_arquivo  # Geração e gravação
from models.rag_engine import retrieve_context                         # Busca com RAG
from models.tradutor_local import traduzir                             # Tradução PT/EN
from datetime import datetime

from controllers.logger import salvar_metricas, log_evento  # <--- NOVO IMPORT

# Conta tokens de um texto (simples split por espaço)


def contar_tokens(texto: str) -> int:
    return len(texto.split())

# Valida se a resposta contém palavras-chave do contexto


def validar_resposta_por_keywords(resposta: str, contexto: str, min_match: int = 3) -> tuple[bool, int]:
    palavras_contexto = re.findall(r'\b\w{4,}\b', contexto.lower())
    palavras_resposta = re.findall(r'\b\w{4,}\b', resposta.lower())
    comuns = set(palavras_contexto).intersection(set(palavras_resposta))
    return len(comuns) >= min_match, len(comuns)

# Função principal que processa cada pergunta


def process_user_input(question: str) -> str:
    log_evento(f"Pergunta recebida: {question}")

    print("\n🔍 [DEBUG] Entrou em process_user_input()")
    print(f"🔍 [DEBUG] Pergunta recebida: {question}")

    # Obtém contexto, scores e dados brutos com debug incluído
    context_pt, scores, context_en, context_norm, debug_ctx = retrieve_context(
        question, return_scores=True, return_raw=True
    )

    print(f"\n📚 [DEBUG] Contexto traduzido (PT, início): {context_pt[:120]}...")

    # Traduz a pergunta para inglês
    question_en = traduzir(question, origem='pt', destino='en')

    # Cria prompt final a ser enviado ao Velvet
    prompt_en = f"Context:\n{debug_ctx['context_en']}\n\nQuestion: {question_en}\nAnswer:"
    print(f"\n🧠 [DEBUG] Prompt final (EN) enviado à Velvet:\n{prompt_en}\n")

    # Mede tempo de geração
    inicio = time.time()
    resposta_en = generate_response(prompt_en)
    duracao = time.time() - inicio

    print(f"\n💬 [DEBUG] Resposta bruta (EN) gerada pelo Velvet:\n{resposta_en.strip()}")

    # Tenta traduzir de volta para português
    try:
        resposta_final = traduzir(resposta_en.strip(), origem="en", destino="pt")
    except Exception as e:
        print("⚠️ Erro na tradução da resposta:", e)
        resposta_final = resposta_en.strip()

    # Validação da resposta com palavras-chave
    valido, num_keywords = validar_resposta_por_keywords(resposta_final, context_pt)
    if not valido or len(resposta_final) < 10:
        resposta_final = "⚠️ Não foi possível gerar uma resposta adequada com base no contexto."

    # Exibe métricas no terminal
    print("\n📊 [MÉTRICAS DE RESPOSTA]")
    print(f"🔸 Prompt Tokens:        {contar_tokens(prompt_en)}")
    print(f"🔸 Resposta Tokens:      {contar_tokens(resposta_en)}")
    print(f"🔸 Tempo de geração:     {duracao:.2f}s")
    print(f"🔸 Palavras-chave comuns: {num_keywords}")
    print(f"🔸 Validação por keywords: {'✅' if valido else '❌'}")

    # Mostra documentos usados com suas pontuações
    print("\n🔸 Similaridade RAG:")
    for i, (trecho, score) in enumerate(scores, start=1):
        preview = trecho.page_content[:80].replace("\n", " ")
        print(f"    Doc#{i}: score={score:.2f} ➜ {preview}...")

    # Guarda métricas em ficheiro próprio
    salvar_metricas({
        "pergunta": question,
        "tempo_execucao": round(duracao, 2),
        "prompt_tokens": contar_tokens(prompt_en),
        "resposta_tokens": contar_tokens(resposta_en),
        "palavras_chave_comuns": num_keywords,
        "validacao_keywords": valido
    })

    # Log técnico detalhado
    log_evento(f"Processada pergunta: {question} | Tokens: {contar_tokens(prompt_en)} prompt, {contar_tokens(resposta_en)} resposta | Tempo: {duracao:.2f}s | Validação: {valido}")

    # Guarda tudo no histórico local com estrutura completa
    salvar_completo_em_arquivo({
        "pergunta_original": question,
        "contexto_pt": context_pt,
        "prompt_enviado": prompt_en,
        "resposta_en": resposta_en.strip(),
        "metricas": {
            "tempo_execucao": round(duracao, 2),
            "prompt_tokens": contar_tokens(prompt_en),
            "resposta_tokens": contar_tokens(resposta_en),
            "palavras_chave_comuns": num_keywords,
            "validacao_keywords": valido
        },
        "scores": [{"doc": trecho.page_content, "score": float(score)} for trecho, score in scores],
        "caminhos_de_gravacao": {
            "historico": "data/respostas/velvet_respostas.json",
            "ultima_resposta": "data/respostas/velvet_ultima_resposta.json"
        },
        "resposta_pt": resposta_final,
        "data": datetime.now().isoformat()
    })
    print(f"\n✅ [DEBUG] Resposta final traduzida (PT):\n{resposta_final}\n")
    return {
        "resposta_pt": resposta_final,
        "tempo_execucao": round(duracao, 2),
        "resposta_tokens": contar_tokens(resposta_en),
        "validacao_keywords": valido
    }
