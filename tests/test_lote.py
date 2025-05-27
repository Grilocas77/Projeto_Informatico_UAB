# ============================================================
# test_lote.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Executa um teste em lote com várias perguntas e mostra resultados

import time
from controllers.chatbot_controller import process_user_input
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Lista de perguntas para o teste em lote
perguntas = [
    "o que é um diagrama de classes?",
    "O que é UML?",
    "o que é um diagrama de casos de utilização?",
    "o que é um diagrama de fluxo de dados?",
    "o que é um diagrama temporal?",
    "Tipos de Diagramas?",
    "Qual a diferença entre um ator primário e um ator secundário?"
]
if __name__ == "__main__":
    print("=== Início do teste em lote ===\n")
    tempo_total = 0

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n🔹 Pergunta #{i}: {pergunta}")
    inicio = time.time()
    resposta = process_user_input(pergunta)
    duracao = time.time() - inicio
    tempo_total += duracao

    if isinstance(resposta, dict):
        print(f"Resposta: {resposta.get('resposta_pt', '')}")
        print(f"Tempo de execução: {resposta.get('tempo_execucao', duracao):.2f} segundos")
        print(f"Tokens: {resposta.get('resposta_tokens', 'N/A')}")
        print(f"Validação: {'✅' if resposta.get('validacao_keywords') else '❌'}")
    else:
        print(f"Resposta: {resposta}")
        print("⚠️ Estrutura inesperada da resposta.")

print(f"\n=== Teste concluído. Tempo total: {tempo_total:.2f} segundos ===")

