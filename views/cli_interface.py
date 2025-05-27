# ============================================================
# cli_interface.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# 🔹 _Interface assíncrona por linha de comandos (CLI) para o chatbot
# 🔹 Suporte a argumentos de linha de comandos (--debug, --simple)
# 🔹 Apresentação colorida com Colorama (compatível com Windows)
# 🔹 Utiliza asyncio para interações não bloqueantes
# 🔹 Integra-se com o controlador principal do chatbot
# 🔹 Histórico de sessão disponível por comando especial (!historico)
# 🔹 Ajuda disponível (!ajuda)
# 🔹 Operaçáo amigável de Ctrl+C
# ============================================================

import asyncio
import sys
import os
import argparse
from colorama import Fore, init

# Inicializa colorama (compatível com Windows)
init(autoreset=True)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controllers.chatbot_controller import process_user_input

# Argumentos da linha de comandos
parser = argparse.ArgumentParser(description="Chatbot CLI com Velvet-2B")
parser.add_argument('--debug', action='store_true', help='Ativar modo de debug completo')
parser.add_argument('--simple', action='store_true', help='Mostrar apenas a resposta final')
args = parser.parse_args()

INSTRUCOES = f"""{Fore.MAGENTA}
Bem-vindo ao Chatbot Velvet-2B (CLI assíncrono)!
Comandos especiais:
  {Fore.YELLOW}!historico{Fore.MAGENTA}  ➔ Mostra o histórico da sessão atual
  {Fore.YELLOW}!ajuda{Fore.MAGENTA}      ➔ Mostra esta mensagem de ajuda
  {Fore.YELLOW}sair{Fore.MAGENTA}        ➔ Termina o chat

Opções:
  {Fore.YELLOW}--debug{Fore.MAGENTA}   ➔ Ativa modo de debug detalhado
  {Fore.YELLOW}--simple{Fore.MAGENTA}  ➔ Só mostra resposta final (ignora prints intermédios)

Comece a conversar! (Ctrl+C para sair a qualquer momento)
"""

# Função principal do _chat
async def chat():
    print(INSTRUCOES)
    historico = []

    try:
        while True:
            pergunta = await asyncio.to_thread(input, Fore.YELLOW + "\nPergunta: ")
            pergunta = pergunta.strip()

            if pergunta.lower() == "sair":
                print(Fore.CYAN + "Sessão terminada. Até à próxima!")
                break

            if pergunta.lower() == "!ajuda":
                print(INSTRUCOES)
                continue

            if pergunta.lower() == "!historico":
                print(Fore.BLUE + "\n=== Histórico desta sessão ===")
                if not historico:
                    print(Fore.BLUE + "Ainda não há interações nesta sessão.")
                else:
                    for i, (q, r) in enumerate(historico, 1):
                        print(Fore.YELLOW + f"{i}. Pergunta: {q}")
                        print(Fore.GREEN + f"   Resposta: {r}\n")
                continue

            if args.debug:
                resposta = await asyncio.to_thread(process_user_input, pergunta)
            else:
                from contextlib import redirect_stdout
                import io
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    resposta = await asyncio.to_thread(process_user_input, pergunta)

            # Apresentação da resposta e métricas
            if isinstance(resposta, dict):
                print(Fore.GREEN + f"\nResposta: {resposta.get('resposta_pt', '')}")
            else:
                print(Fore.GREEN + f"\nResposta: {resposta}")

            # Mostrar métricas se existirem
            if isinstance(resposta, dict):
                print(Fore.CYAN + "\n--- Métricas da Resposta ---")
                print(f"Tempo de execução: {resposta.get('tempo_execucao', 0):.2f} segundos")
                print(f"Número de tokens na resposta: {resposta.get('resposta_tokens', 'N/A')}")
                print(f"Validação por palavras-chave: {'✅ Sim' if resposta.get('validacao_keywords') else '❌ Não'}")
            else:
                print(Fore.RED + "\n[Aviso] Estrutura inesperada da resposta – não foi possível mostrar métricas.")

            resposta_final = resposta.get('resposta_pt', resposta) if isinstance(resposta, dict) else resposta
            historico.append((pergunta, resposta_final))

    except KeyboardInterrupt:
        print(Fore.CYAN + "\nSessão interrompida com Ctrl+C. Até à próxima!\n")

if __name__ == "__main__":
    asyncio.run(chat())
