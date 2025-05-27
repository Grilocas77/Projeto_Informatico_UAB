# 🧠 Chatbot Educativo com Velvet-2B e RAG

Projeto desenvolvido por **Duarte Grilo (2201320)** no âmbito da unidade curricular de **Projeto Informático (UAb)**.

## 🎯 Objetivo

Criar um **chatbot educativo open source** capaz de responder a perguntas com base em materiais reais de uma Unidade Curricular da área de Informática, utilizando:

- **LLM local (Velvet-2B)**
- **Técnica de RAG (Retrieval-Augmented Generation)**
- **Tradução automática (PT ⇄ EN)**
- **Interfaces CLI, GUI e Discord**

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- HuggingFace Transformers
- LangChain (componentes individuais)
- ChromaDB (vector store local)
- MarianMT (tradução local)
- Tkinter (GUI)
- Colorama (CLI)

## 🗂️ Estrutura do Projeto

```plaintext
├── controllers/            # Lógica principal e orquestração
├── models/                 # RAG, geração, tradução, persistência
├── views/                  # Interfaces (CLI, GUI, Discord)
├── tests/                  # Scripts de teste e geração de métricas
├── data/documents/         # Base de conhecimento (PDFs, .txt)
├── embeddings_db/         # Embeddings ChromaDB
└── assets/                # Imagens e ícones da interface

