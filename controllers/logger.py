# ============================================================
# logger.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Este módulo é responsável por:
# 🔹 Guardar métricas detalhadas das respostas do chatbot
#     - Salva cada métrica como linha JSON (velvet_metrics.jsonl)
# 🔹 Registar eventos técnicos e de sistema em log textual
#     - Regista cada evento no ficheiro velvet_logs.txt
# 🔹 Garantir que os diretórios de dados e logs existem
# 🔹 Acrescentar timestamps a todas as entradas de métricas e logs
# ============================================================

import json
import os
from datetime import datetime


def salvar_metricas(metricas, caminho="data/metrics/velvet_metrics.jsonl"):
    """Acrescenta uma linha JSON com métricas ao ficheiro velvet_metrics.jsonl"""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    metricas["timestamp"] = datetime.now().isoformat()
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(metricas, ensure_ascii=False) + "\n")


def log_evento(msg, caminho="logs/velvet_logs.txt"):
    """Acrescenta um evento ao ficheiro de _logs técnicos"""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
