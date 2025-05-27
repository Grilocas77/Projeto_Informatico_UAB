# ============================================================
# test_request.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# Este script analisa o histórico de respostas do chatbot Velvet-2B.
#
# Funcionalidades:
# 🔹 Carrega e processa o ficheiro `velvet_respostas.json`
# 🔹 Calcula métricas: tempo, validade, número de tokens e documentos
# 🔹 Identifica e guarda respostas inválidas
# 🔹 Gera relatórios em CSV, JSON e Markdown
# 🔹 Cria gráfico com as perguntas mais frequentes
# ============================================================

import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from pathlib import Path


# Diretórios de entrada e saída (ajustados para uso local)
entrada_json = Path("data/respostas/velvet_respostas.json")
saida_dir = Path("tests/relatorios")
saida_dir.mkdir(parents=True, exist_ok=True)


# Leitura do JSON de respostas
with open(entrada_json, 'r', encoding='utf-8') as f:
    respostas = json.load(f)

# Inicializar listas para o DataFrame
dados_metricas = []
respostas_invalidas = []
frequencia_perguntas = Counter()

# Processamento de cada entrada
for entrada in respostas:
    pergunta = entrada.get("pergunta_original", "").strip()
    resposta = entrada.get("resposta_pt", "").strip()
    tempo = entrada.get("tempo_execucao", 0)
    valido = entrada.get("validacao_keywords", False)
    num_docs = len(entrada.get("scores", []))
    data_hora = entrada.get("data", "N/A")
    context_pt = entrada.get("context_pt", "")

    frequencia_perguntas[pergunta] += 1

    if not valido or len(resposta) < 10 or context_pt.strip() == "":
        respostas_invalidas.append(entrada)

    dados_metricas.append({
        "pergunta": pergunta,
        "valida": valido,
        "tempo_execucao": tempo,
        "num_documentos": num_docs,
        "resposta_tokens": len(resposta.split()),
        "data_hora": data_hora
    })

# Criar DataFrames
df_metricas = pd.DataFrame(dados_metricas)
df_perguntas = pd.DataFrame(frequencia_perguntas.items(), columns=["pergunta", "frequencia"])

# Guardar CSVs
df_metricas.to_csv(saida_dir / "resumo_metricas.csv", index=False)
df_perguntas.to_csv(saida_dir / "ranking_perguntas.csv", index=False)

# Guardar JSON com respostas inválidas
with open(saida_dir / "respostas_invalidas.json", 'w', encoding='utf-8') as f_out:
    json.dump(respostas_invalidas, f_out, ensure_ascii=False, indent=2)

# Criar gráfico de barras
plt.figure(figsize=(10, 6))
top_perguntas = df_perguntas.sort_values(by="frequencia", ascending=False).head(10)
plt.barh(top_perguntas["pergunta"], top_perguntas["frequencia"])
plt.xlabel("Frequência")
plt.title("Top 10 Perguntas Mais Frequentes")
plt.gca().invert_yaxis()
grafico_path = saida_dir / "grafico_perguntas_frequentes.png"
plt.tight_layout()
plt.savefig(grafico_path)

# Criar relatório markdown
relatorio_md = saida_dir / "relatorio_respostas.md"
with open(relatorio_md, "w", encoding="utf-8") as f_md:
    f_md.write("# Relatório de Respostas do Chatbot Velvet-2B\n\n")
    f_md.write("Este relatório foi gerado automaticamente com base no histórico de respostas guardado no ficheiro `velvet_respostas.json`.\n\n")
    f_md.write("## Top 10 Perguntas Mais Frequentes\n\n")
    f_md.write(top_perguntas.to_markdown(index=False))
    f_md.write("\n\n![Gráfico](grafico_perguntas_frequentes.png)\n\n")
    f_md.write("## Resumo de Métricas por Pergunta\n\n")
    f_md.write(df_metricas.head(10).to_markdown(index=False))
    f_md.write("\n\n## Respostas Inválidas Detetadas\n\n")
    f_md.write(f"Foram detetadas {len(respostas_invalidas)} respostas inválidas. Detalhes no ficheiro `respostas_invalidas.json`.\n")
