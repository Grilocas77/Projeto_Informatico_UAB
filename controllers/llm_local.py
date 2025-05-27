# Mini LLM Local - Consolidado (com feedback supervisionado)

from PIL import UnidentifiedImageError
import os
import json
from sentence_transformers import CrossEncoder
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Toplevel
from PIL import Image, ImageTk
from datetime import datetime
from models.velvet_runner import generate_response


CHROMA_PATH = "embeddings_db/chroma_db"
EMBEDDING_MODEL = "intfloat/e5-large-v2"
RESPOSTAS_MEMORIA = "data/respostas/respostas_memoria.json"

embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def normalizar_pergunta(texto):
    return (
        texto.strip()
             .lower()
             .replace("?", "")
             .replace(".", "")
             .replace(",", "")
             .replace("!", "")
    )


def salvar_resposta_memoria(pergunta, contexto, score, origem, pagina):
    caminho = os.path.join("data", "respostas", "respostas_memoria.json")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    pergunta_key = normalizar_pergunta(pergunta)

    # Ler estrutura atual, que pode ser lista (antiga) ou dicionário (novo)
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)

            # Se for lista, migrar para dicionário
            if isinstance(dados, list):
                novo_dados = {}
                for entrada in dados:
                    key = normalizar_pergunta(entrada.get("pergunta", ""))
                    if key:
                        novo_dados[key] = {
                            "contexto": entrada.get("contexto", ""),
                            "score": float(entrada.get("score", 0)),
                            "fonte": entrada.get("fonte", "?"),
                            "pagina": entrada.get("pagina", "?"),
                            "timestamp": entrada.get("data", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        }
                dados = novo_dados
        except json.JSONDecodeError:
            dados = {}
    else:
        dados = {}

    # Guardar nova resposta
    dados[pergunta_key] = {
        "contexto": contexto,
        "score": float(score),
        "fonte": origem,
        "pagina": pagina,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Escrever no ficheiro
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"💾 Contexto memorizado (normalizado) para: '{pergunta_key}'")


def busca_local_heuristica(pergunta: str, k: int = 5, forcar_popup=False):
    pergunta_key = normalizar_pergunta(pergunta)
    caminho = "data/respostas/respostas_memoria.json"

    print(f"\n🔍 Pergunta feita: {pergunta}")
    print(f"🔑 Chave normalizada: {pergunta_key}")
    print(f"📁 Verificando memória em: {caminho}")

    if not forcar_popup and os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                memoria = json.load(f)
                print(f"📘 Memória carregada com {len(memoria)} entradas.")
            if pergunta_key in memoria:
                item = memoria[pergunta_key]
                print("✅ Entrada encontrada na memória!")
                resposta = f"{item['contexto'].strip()}\n\n📄 Fonte: {item['fonte']} (pág. {item['pagina']})"
                return resposta, None
            else:
                print("❌ Entrada NÃO encontrada na memória.")
        except Exception as e:
            print(f"⚠️ Erro ao ler memória: {e}")
    else:
        if forcar_popup:
            print("⚠️ Popup forçado manualmente (forcar_popup=True)")
        elif not os.path.exists(caminho):
            print("🚫 Ficheiro de memória não encontrado.")

    # Recorre ao RAG normal se não encontrou na memória
    print("🔎 Gerando nova resposta com RAG...")

    pergunta_formatada = f"query: {pergunta}"
    resultados = vectorstore.similarity_search_with_score(pergunta_formatada, k=k)
    docs = [doc for doc, _ in resultados if doc]
    pairs = [(pergunta, doc.page_content) for doc in docs if doc.page_content]
    scores = _reranker.predict(pairs)
    reranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)

    return None, reranked[:3]


def gerar_resposta_final(pergunta, contexto):
    prompt = f"{contexto}\n\nPergunta: {pergunta}\nResposta:"
    resposta = generate_response(prompt)  # Esta deve vir do teu modelo (Velvet ou outro)
    return resposta


def run_chatbot_gui():
    def enviar_pergunta():
        pergunta = entrada_pergunta.get().strip()
        if not pergunta:
            return
        resposta, contextos = busca_local_heuristica(pergunta)

        if resposta:
            chat_box.config(state="normal")
            chat_box.insert(tk.END, f"\n\n❓ {pergunta}\n🧠 {resposta}\n")
            chat_box.config(state="disabled")
            chat_box.see(tk.END)
            entrada_pergunta.delete(0, tk.END)
            salvar_log(pergunta, resposta)
        elif contextos:
            mostrar_popup_selecao(pergunta, contextos)
        else:
            messagebox.showinfo("Erro", "Não foi possível gerar resposta.")

    def mostrar_popup_selecao(pergunta, top3):
        popup = Toplevel(janela)
        popup.title("Selecionar melhor contexto")
        popup.geometry("750x500")
        popup.configure(bg="#f4f4f4")

        selecao = tk.IntVar(value=0)
        textos = []

        for i, (doc, score) in enumerate(top3):
            frame = tk.Frame(popup, bd=1, relief="solid", padx=5, pady=5, bg="#ffffff")
            frame.pack(fill="x", padx=10, pady=5)

            origem = doc.metadata.get("source", "?")
            pagina = doc.metadata.get("page", "?")

            texto = f"#{i + 1} | Score: {round(score, 4)}\nFonte: {origem} (pág. {pagina})\n"
            textos.append((doc.page_content, score, origem, pagina))

            # Texto + botão de seleção
            ttk.Radiobutton(frame, text=f"Selecionar contexto #{i + 1}", variable=selecao, value=i).pack(anchor="w",
                                                                                                         padx=5, pady=2)

            scrolled = scrolledtext.ScrolledText(frame, wrap="word", height=6, font=("Arial", 10), bg="#f9f9f9")
            scrolled.insert("1.0", texto + "\n" + doc.page_content)
            scrolled.configure(state="disabled")
            scrolled.pack(fill="x", padx=5)

        # === Botão de confirmar ===
        def confirmar():
            idx = selecao.get()
            contexto_escolhido = textos[idx][0]
            popup.destroy()
            # Aqui podes passar a variável `contexto_escolhido` para uso posterior, como gerar a resposta
            resposta_final = gerar_resposta_final(pergunta, contexto_escolhido)
            mostrar_resposta_no_chatbox(pergunta, resposta_final)

        botao_confirmar = tk.Button(popup, text="Confirmar", command=confirmar, bg="#4CAF50", fg="white",
                                    font=("Arial", 11, "bold"))
        botao_confirmar.pack(pady=10)

    def salvar_log(pergunta, resposta):
        os.makedirs("logs", exist_ok=True)
        with open("logs/conversa_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\nPergunta: {pergunta}\nResposta: {resposta}\n\n")

    def mostrar_resposta_no_chatbox(pergunta, resposta):
        chat_box.config(state="normal")
        chat_box.insert(tk.END, f"\n\n❓ {pergunta}\n🧠 {resposta}\n")
        chat_box.config(state="disabled")
        chat_box.see(tk.END)
        entrada_pergunta.delete(0, tk.END)
        salvar_log(pergunta, resposta)

    def limpar_chat():
        chat_box.config(state="normal")
        chat_box.delete("1.0", tk.END)
        chat_box.insert(tk.END, "💬 Chat reiniciado.\n")
        chat_box.config(state="disabled")

    def sair():
        if messagebox.askokcancel("Sair", "Deseja realmente sair do chatbot?"):
            janela.destroy()

    janela = tk.Tk()
    janela.title("Mini Chatbot Local (LLM)")
    janela.geometry("700x550")
    janela.configure(bg="#f4f4f4")

    try:
        logo_path = os.path.join("assets", "logoUAb.png")
        logo = Image.open(logo_path).resize((120, 120))
        logo_img = ImageTk.PhotoImage(logo)
        logo_label = tk.Label(janela, image=logo_img, bg="#f4f4f4")  # type: ignore
        logo_label.image = logo_img  # manter referência viva
        logo_label.pack(pady=5)

    except FileNotFoundError:
        print("❌ Logo não encontrado no caminho indicado.")
    except UnidentifiedImageError:
        print("❌ O ficheiro não é uma imagem válida.")
    except Exception as e:
        print(f"⚠️ Erro inesperado ao carregar o logo: {e}")

    ttk.Label(janela, text="Chatbot Local - Base Semântica", font=("Arial", 14, "bold")).pack(pady=5)
    total_docs = len(vectorstore.get())
    ttk.Label(janela, text=f"📚 Documentos carregados: {total_docs}", font=("Arial", 10)).pack(pady=2)

    chat_box = scrolledtext.ScrolledText(janela, wrap="word", font=("Courier New", 11), height=18)
    chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    chat_box.insert(tk.END, "💬 Bem-vindo ao Chatbot IA Local!\n")
    chat_box.config(state="disabled")

    entrada_frame = tk.Frame(janela)
    entrada_frame.pack(pady=5, fill=tk.X, padx=10)
    entrada_pergunta = ttk.Entry(entrada_frame, font=("Arial", 11))
    entrada_pergunta.pack(side=tk.LEFT, fill=tk.X, expand=True)
    entrada_pergunta.bind("<Return>", lambda e: enviar_pergunta())

    ttk.Button(entrada_frame, text="Enviar", command=enviar_pergunta).pack(side=tk.LEFT, padx=5)
    ttk.Button(janela, text="🧹 Limpar chat", command=limpar_chat).pack(pady=2)
    ttk.Button(janela, text="❌ Sair", command=sair).pack(pady=5)

    janela.mainloop()


if __name__ == "__main__":
    run_chatbot_gui()
