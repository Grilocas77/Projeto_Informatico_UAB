# ============================================================
# config.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# Definir as configurações centrais do sistema, incluindo:
#
# 🔹 Diretórios principais (documentos, embeddings)
# 🔹 Modelos utilizados (embeddings, reranker, LLM, tradução)
# 🔹 _Tokens e parâmetros para APIs externas (HuggingFace, Discord)
# 🔹 Parâmetros para geração de respostas e processamento de texto
# 🔹 _Templates e constantes usados em diversos módulos
# ============================================================

import os
from dotenv import load_dotenv
from transformers import MarianMTModel, MarianTokenizer

# 🔹 Carrega variáveis de ambiente a partir do ficheiro .env (ex: tokens API)
load_dotenv()

# 🔹 Diretórios principais do projeto
DOCUMENTS_PATH = "data/documents"          # Onde ficam os ficheiros a indexar
CHROMA_PATH = "embeddings_db/chroma_db"    # Caminho para a base de embeddings ChromaDB

# 🔹 Modelos a utilizar
EMBEDDING_MODEL = "intfloat/e5-large-v2"   # Modelo de embeddings semânticos
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Modelo para reranking
VELVET_MODEL = "Almawave/Velvet-2B"        # Modelo de linguagem principal (LLM)

# 🔹 Token da Hugging Face (para acesso aos modelos online)
HF_TOKEN = os.getenv("HF_TOKEN")

# 🔹 Tradutores pré-carregados com MarianMT (usados no módulo tradutor_local.py)
TRADUTOR_MODELOS = {
    "pt-en": {
        "tokenizer": MarianTokenizer.from_pretrained("geralt/Opus-mt-pt-en"),
        "model": MarianMTModel.from_pretrained("geralt/Opus-mt-pt-en")
    },
    "en-pt": {
        "tokenizer": MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-tc-big-en-pt"),
        "model": MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-tc-big-en-pt")
    }
}

# 🔹 Token do bot do Discord (se usado)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 🔹 Parâmetros de geração do modelo Velvet
VELVET_PARAMS = {
    "max_new_tokens": 300,          # Número máximo de tokens gerados
    "do_sample": True,              # Ativa amostragem
    "temperature": 0.3,             # Temperatura baixa = respostas mais determinísticas
    "top_p": 0.8,                   # Nucleus sampling
    "repetition_penalty": 1.2       # Penaliza repetições
}

# 🔹 _Template para geração de prompts no modo CLI/GUI
CHATBOT_PROMPT_TEMPLATE = (
    "Contexto:\n{contexto}\n\n"
    "Pergunta: {user_input}\n"
    "Resposta:"
)

# 🔹 Parâmetros usados no split e busca de documentos (RAG)
CHUNK_SIZE = 1200             # Tamanho de cada chunk (bloco de texto)
CHUNK_OVERLAP = 200          # Sobreposição entre chunks para não perder contexto
K_SIMILARITY_SEARCH = 7      # Número de documentos mais semelhantes a retornar

# Parâmetro para _top-k documentos retornados nas buscas semânticas
TOP_K_SEARCH = 5

# Limite de caracteres da resposta que é apresentada ao utilizador
MAX_DOC_CHARS = 800

MAX_PROMPT_TOKENS = 512
