# ============================================================
# metrics_controller_local.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Este módulo é responsável por:
# 🔹 Analisar localmente as respostas do Velvet-2B guardadas no histórico
# 🔹 Gerar métricas: tempo, tokens, taxa de respostas válidas, etc.
# 🔹 Gerar relatórios:
#     - Markdown (.md)
#     - Gráficos (.png)
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

# Caminho do histórico de respostas
respostas_path = Path("data/respostas/velvet_respostas.json")
relatorio_md_path = Path("tests/relatorios/relatorio_velvet_local.md")
grafico_tempo_path = Path("tests/relatorios/grafico_tempo_velvet.png")
grafico_valida_path = Path("tests/relatorios/grafico_valida_velvet.png")

# Verifica se o ficheiro existe
if not respostas_path.exists():
    print(f"⚠️ O ficheiro {respostas_path} não foi encontrado.")
    exit()

# Lê todas as respostas
with open(respostas_path, encoding="utf-8") as f:
    respostas = json.load(f)

# Extrai métricas (ignora respostas sem campo 'metricas')
dados_metricas = []
for resp in respostas:
    metricas = resp.get("metricas")
    if metricas:
        dados_metricas.append({
            "data": resp.get("data", ""),
            "pergunta": resp.get("pergunta_original", ""),
            "tempo_execucao": metricas.get("tempo_execucao"),
            "prompt_tokens": metricas.get("prompt_tokens"),
            "resposta_tokens": metricas.get("resposta_tokens"),
            "palavras_chave_comuns": metricas.get("palavras_chave_comuns"),
            "validacao_keywords": metricas.get("validacao_keywords"),
        })

if not dados_metricas:
    print("⚠️ Não foram encontradas métricas válidas no histórico.")
    exit()

df = pd.DataFrame(dados_metricas)

# Estatísticas principais
tempo_medio = round(df['tempo_execucao'].mean(), 2)
taxa_validas = round(df['validacao_keywords'].mean() * 100, 1)
tokens_medio = round(df['resposta_tokens'].mean(), 1)
total_respostas = len(df)

# Cria gráfico de distribuição dos tempos de resposta
plt.figure(figsize=(8, 4))
df['tempo_execucao'].plot(kind="hist", bins=20, color="#3399ff",
                          title="Distribuição dos Tempos de Resposta (Velvet-2B)")
plt.xlabel("Tempo de resposta (s)")
plt.ylabel("Frequência")
plt.grid(True)
plt.tight_layout()
plt.savefig(grafico_tempo_path)
plt.close()

# Gráfico da taxa de respostas válidas ao longo do tempo
plt.figure(figsize=(8, 4))
df['validacao_keywords'].rolling(window=20, min_periods=1).mean().plot(title="Taxa Móvel de Respostas Válidas (Velvet-2B)")
plt.ylabel("Taxa de respostas válidas (média móvel)")
plt.xlabel("Índice da interação")
plt.ylim(0, 1)
plt.grid(True)
plt.tight_layout()
plt.savefig(grafico_valida_path)
plt.close()

# Gera relatório markdown
with open(relatorio_md_path, "w", encoding="utf-8") as f_md:
    f_md.write(f"# Relatório Local de Métricas do Velvet-2B\n\n")
    f_md.write(f"**Total de respostas analisadas:** {total_respostas}\n\n")
    f_md.write(f"- Tempo médio de resposta: **{tempo_medio} segundos**\n")
    f_md.write(f"- Taxa de respostas válidas: **{taxa_validas}%**\n")
    f_md.write(f"- Tokens médios por resposta: **{tokens_medio}**\n\n")
    f_md.write(f"## Distribuição dos Tempos de Resposta\n")
    f_md.write(f"![Gráfico Tempo](grafico_tempo_velvet.png)\n\n")
    f_md.write(f"## Taxa de Respostas Válidas ao Longo do Tempo\n")
    f_md.write(f"![Gráfico Validação](grafico_valida_velvet.png)\n\n")
    f_md.write(f"## Primeiras 10 métricas:\n\n")
    f_md.write(df.head(10).to_markdown(index=False))
    f_md.write("\n")

print("✅ Relatório local gerado com sucesso!")

