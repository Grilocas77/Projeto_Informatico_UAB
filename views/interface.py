# ============================================================
# interface.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# Interface gráfica principal (Tkinter) para gestão do chatbot educativo.
#
# Funcionalidades:
# 🔹 Inicia interfaces: CLI, GUI local e bot Discord
# 🔹 Executa scripts auxiliares: métricas, testes
# 🔹 Acede a ficheiros de resultados e logs
# 🔹 Gera logs e mostra estado atual
# 🔹 GESTÃO CENTRALIZADA DA BIBLIOTECA RAG
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import subprocess
import os
import platform
from datetime import datetime
import threading
import json
from models.rag_library_manager import RAGLibraryManager


# ========== Strings para Internacionalização ==========
STRINGS = {
    "title": "Painel de Controle do Chatbot Educativo (Velvet + RAG)",
    "interfaces": "INTERFACES",
    "cli": "Iniciar CLI",
    "gui_local": "Iniciar Chatbot Local (IA Interna)",
    "discord": "Iniciar Bot Discord",
    "processing": "PROCESSAMENTO",
    "rag": "Gerir Biblioteca RAG",
    "test": "Gerar Respostas de Teste",
    "metrics": "Avaliar Métricas",
    "files": "FICHEIROS",
    "open_json": "Abrir velvet_respostas.json",
    "open_csv": "Abrir Relatório Comparativo (.csv)",
    "open_log": "Abrir Log do Painel",
    "config": "Configurações",
    "exit": "Sair",
    "confirm_exit": "Tens a certeza que queres sair?",
    "status_ready": "🟢 Pronto",
    "python_missing": "Python do venv não encontrado: {path}",
    "script_not_found": "Script não encontrado: {path}",
    "error_running": "Erro ao executar {desc}.",
    "running": "A executar {desc}...",
    "done": "{desc} concluído.",
    "log_opened": "Log do painel aberto.",
    "log_not_found": "Ficheiro de log não existe.",
    "choose_script": "Selecionar novo caminho para {desc}",
    "choose_asset": "Selecionar novo caminho para {desc}",
    "config_saved": "Configurações guardadas.",
    "tooltip_cli": "Abre a interface de linha de comandos (CLI) do chatbot.",
    "tooltip_gui": "Abre a interface gráfica local do chatbot.",
    "tooltip_discord": "Inicia o bot Discord integrado.",
    "tooltip_rag": "Abrir gestor da biblioteca vetorial RAG.",
    "tooltip_test": "Executa testes automáticos (gera respostas de teste).",
    "tooltip_metrics": "Abre o painel de avaliação de métricas.",
    "tooltip_json": "Abre o ficheiro velvet_respostas.json para consulta.",
    "tooltip_csv": "Abre um ficheiro .csv de comparação de respostas.",
    "tooltip_log": "Abre o ficheiro de log do painel de controlo.",
    "tooltip_config": "Abrir janela de configurações (paths e preferências).",
    "tooltip_exit": "Fecha o painel de controlo.",
}

# ========== Configurações e Paths ==========
CONFIG_PATH = "config/painel_config.json"
DEFAULT_CONFIG = {
    "PYTHON_EXEC": os.path.join(os.getcwd(), "venv", "Scripts", "python.exe"),
    "SCRIPT_PATHS": {
        "cli": "views/cli_interface.py",
        "discord": "views/discord_interface.py",
        "metrics": "tests/metrics_controller.py",
        "test_request": "tests/test_request.py",
        "test_lote": "tests/test_lote.py",
    },
    "ASSET_PATHS": {
        "background": "assets/background.jpg",
        "logo": "assets/logoUAb.png",
    },
    "DATA_PATHS": {
        "respostas_json": "data/respostas/velvet_respostas.json",
        "data_dir": "data",
    },
    "LOG_PATH": "logs/painel_log.txt"
}
config = DEFAULT_CONFIG.copy()

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config.update(json.load(config_file))

# ========== Logging ==========


def salvar_log(msg: str):
    log_path = config["LOG_PATH"]
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

# ========== Utilitários ==========


def abrir_ajuda():
    ajuda = tk.Toplevel(root)
    ajuda.title("Sobre o Projeto")
    ajuda.geometry("500x400")
    ttk.Label(ajuda, text="📘 Sobre o Chatbot Educativo Velvet + RAG", style="Title.TLabel").pack(pady=10)

    texto = (
        "Este painel de controlo foi desenvolvido por Duarte Grilo (2201320) no contexto do Projeto Informático (UAb).\n\n"
        "Funcionalidades principais:\n"
        "- Gestão de interfaces (CLI, GUI, Discord)\n"
        "- Integração com modelos LLM (Velvet-2B, ChatGPT)\n"
        "- Geração e avaliação de respostas com métricas\n"
        "- Biblioteca vetorial RAG\n\n"
        "📁 Estrutura modular e configurável via JSON\n"
        "🧠 Modelos: Almawave/Velvet-2B, OpenAI GPT-3.5\n\n"
        "🔗 Documentação:\n"
        "https://github.com/Grilocas77/Chatbot_educativo\n\n"
        "Versão: 1.0\n"
    )

    msg = tk.Message(ajuda, text=texto, width=480, font=("Arial", 10))
    msg.pack(pady=10)

    ttk.Button(ajuda, text="Fechar", command=ajuda.destroy).pack(pady=20)


def mostrar_erro(msg: str, exc: Exception = None):
    detalhes = f"\n\nDetalhes: {exc}" if exc else ""
    messagebox.showerror("Erro", f"{msg}{detalhes}")
    salvar_log(f"ERRO: {msg}{detalhes}")


def mostrar_info(msg: str):
    messagebox.showinfo("Info", msg)
    salvar_log(msg)


def validar_arquivo(caminho: str, descricao: str) -> bool:
    print(f"[DEBUG] Validando existência de: {caminho}")
    if not os.path.exists(caminho):
        mostrar_erro(STRINGS["script_not_found"].format(path=caminho))
        return False
    return True


def validar_python():
    caminho = config["PYTHON_EXEC"]
    if not os.path.exists(caminho):
        mostrar_erro(STRINGS["python_missing"].format(path=caminho))
        return False
    return True


def executar_script(script_key: str, descricao: str, args=None):
    script_path = config["SCRIPT_PATHS"].get(script_key)
    python_exec = config["PYTHON_EXEC"]

    print(f"[DEBUG] Script key: {script_key} → {script_path}")
    print(f"[DEBUG] Python exec: {python_exec}")
    print(f"[DEBUG] Script path: {script_path}")

    if not validar_python() or not validar_arquivo(script_path, descricao):
        return

    comando = [config["PYTHON_EXEC"], "-m", script_path.replace("/", ".").replace(".py", "")]
    if args:
        comando.extend(args)

    print("[DEBUG] Comando completo para execução:", " ".join(f'"{c}"' if " " in c else c for c in comando))

    running_win = tk.Toplevel(root)
    running_win.title(STRINGS["running"].format(desc=descricao))
    ttk.Label(running_win, text=STRINGS["running"].format(desc=descricao), padding=10).pack()
    running_win.geometry("300x80")
    running_win.transient(root)
    running_win.grab_set()
    running_win.update()

    def run_and_monitor():
        try:
            proc = subprocess.Popen(
                comando,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            proc.wait()
            if proc.returncode == 0:
                msg = STRINGS["done"].format(desc=descricao)
                mostrar_info(msg)
                atualizar_status(msg)
            else:
                mostrar_erro(STRINGS["error_running"].format(desc=descricao))
                atualizar_status(STRINGS["error_running"].format(desc=descricao))
        except Exception as exc:
            mostrar_erro(STRINGS["error_running"].format(desc=descricao), exc)
        finally:
            running_win.destroy()

    threading.Thread(target=run_and_monitor, daemon=True).start()


# ========== Funções Específicas ==========


def run_cli(event=None): executar_script("cli", STRINGS["cli"])
def run_discord(): executar_script("discord", STRINGS["discord"])


def run_llm_local_gui():
    try:
        from controllers.llm_local import run_chatbot_gui
        run_chatbot_gui()
        salvar_log("Mini LLM Local (GUI) iniciado com sucesso.")
        atualizar_status("Mini LLM Local iniciado com sucesso.")
    except Exception as exc:
        mostrar_erro("Erro ao iniciar o GUI local.", exc)


def run_test_request(): executar_script("test_request", STRINGS["test"])
def run_metrics(): executar_script("metrics", STRINGS["metrics"])


def executar_teste_lote():
    executar_script("test_lote", "Teste em Lote")


def open_respostas_json():
    caminho = os.path.abspath(config["DATA_PATHS"]["respostas_json"])
    if not validar_arquivo(caminho, STRINGS["open_json"]):
        return
    abrir_ficheiro(caminho)
    salvar_log("Arquivo velvet_respostas.json aberto.")
    atualizar_status("Arquivo velvet_respostas.json aberto.")


def open_csv_comparativo():
    pasta = os.path.abspath(config["DATA_PATHS"]["data_dir"])
    filepath = filedialog.askopenfilename(
        initialdir=pasta,
        title=STRINGS["open_csv"],
        filetypes=[("Arquivos CSV", "*.csv")]
    )
    if filepath:
        abrir_ficheiro(filepath)
        salvar_log(f"Arquivo comparativo aberto: {filepath}")
        atualizar_status(f"Arquivo comparativo aberto: {os.path.basename(filepath)}")


def abrir_ficheiro(caminho):
    try:
        caminho_absoluto = os.path.abspath(caminho)
        print("🔍 Caminho absoluto para abrir:", caminho_absoluto)

        if os.name == 'nt':  # Windows
            os.startfile(caminho_absoluto)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", caminho_absoluto], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", caminho_absoluto], check=True)
    except Exception as e:
        # Fallback para abrir com o Notepad no Windows
        if os.name == 'nt':
            try:
                subprocess.run(["notepad", caminho_absoluto])
            except Exception as fallback_error:
                mostrar_erro("Erro ao abrir com o Notepad.", fallback_error)
        else:
            mostrar_erro("Erro ao abrir o ficheiro.", e)


def open_log():
    log_path = config["LOG_PATH"]
    try:
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Cria o ficheiro se não existir
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")

        abrir_ficheiro(log_path)
        atualizar_status(STRINGS["log_opened"])
    except Exception as e:
        mostrar_erro("Erro ao abrir o ficheiro de log.", e)


# ========== Gestão Centralizada da Biblioteca RAG ==========


def abrir_rag_library_manager():

    janela = tk.Toplevel(root)
    janela.title("Gestão Biblioteca RAG")
    janela.geometry("420x260")
    ttk.Label(janela, text="Gestão da Biblioteca Vetorial RAG", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=10)

    manager = RAGLibraryManager()

    # --- Barra de progresso ---
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(janela, variable=progress_var, maximum=100, length=350, mode='determinate')
    progress_bar.grid(row=3, column=0, columnspan=2, pady=18)
    progress_label = ttk.Label(janela, text="Progresso: 0%")
    progress_label.grid(row=4, column=0, columnspan=2)

    def update_progress(current, total):
        percent = int((current / total) * 100)
        progress_var.set(percent)
        progress_label.config(text=f"Progresso: {percent}%")
        janela.update_idletasks()

    def executar_build():
        def run():
            try:
                manager.build(force_rebuild=True, progress_callback=update_progress)
                progress_var.set(100)
                progress_label.config(text="Progresso: 100%")
                mostrar_info("Base vetorial reconstruída com sucesso.")
                atualizar_status("Rebuild RAG concluído.")
            except Exception as exc:
                mostrar_erro("Erro ao reconstruir biblioteca RAG.", exc)
                atualizar_status("Erro ao reconstruir biblioteca RAG.")
        threading.Thread(target=run, daemon=True).start()

    def executar_update():
        def run():
            try:
                manager.update(progress_callback=update_progress)
                progress_var.set(100)
                progress_label.config(text="Progresso: 100%")
                mostrar_info("Base vetorial atualizada com sucesso.")
                atualizar_status("Update RAG concluído.")
            except Exception as exc:
                mostrar_erro("Erro ao atualizar biblioteca RAG.", exc)
                atualizar_status("Erro ao atualizar biblioteca RAG.")
        threading.Thread(target=run, daemon=True).start()

    ttk.Button(janela, text="Update Incremental", width=25, command=executar_update).grid(row=1, column=0, pady=5, padx=10)
    ttk.Button(janela, text="Rebuild Completo", width=25, command=executar_build).grid(row=1, column=1, pady=5, padx=10)
    ttk.Button(janela, text="Fechar", width=25, command=janela.destroy).grid(row=2, column=0, columnspan=2, pady=20)

# ========== Configurações ==========


def open_config():
    win = tk.Toplevel(root)
    win.title(STRINGS["config"])
    win.geometry("600x400")
    row = 0

    def choose_new_path(script_key, desc, dict_ref):
        newpath = filedialog.askopenfilename(
            title=STRINGS["choose_script"].format(desc=desc) if script_key in config["SCRIPT_PATHS"] else STRINGS["choose_asset"].format(desc=desc)
        )
        if newpath:
            dict_ref[script_key] = newpath
            atualizar_status(f"{desc} atualizado.")

    ttk.Label(win, text="Caminhos dos Scripts", style="Title.TLabel").grid(row=row, column=0, pady=5, sticky="w")
    for script_key, script_value in config["SCRIPT_PATHS"].items():
        ttk.Label(win, text=f"{script_key}:").grid(row=row+1, column=0, sticky="w", padx=10)
        ttk.Entry(win, width=50, textvariable=tk.StringVar(value=script_value)).grid(row=row+1, column=1)
        ttk.Button(win, text="Alterar", command=lambda key=script_key: choose_new_path(key, key, config["SCRIPT_PATHS"])).grid(row=row+1, column=2)
        row += 1

    ttk.Label(win, text="Caminhos dos Assets", style="Title.TLabel").grid(row=row, column=0, pady=5, sticky="w")
    for asset_key, asset_value in config["ASSET_PATHS"].items():
        ttk.Label(win, text=f"{asset_key}:").grid(row=row+1, column=0, sticky="w", padx=10)
        ttk.Entry(win, width=50, textvariable=tk.StringVar(value=asset_value)).grid(row=row+1, column=1)
        ttk.Button(win, text="Alterar", command=lambda key=asset_key: choose_new_path(key, key, config["ASSET_PATHS"])).grid(row=row+1, column=2)
        row += 1

    def guardar():
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=2)
        mostrar_info(STRINGS["config_saved"])
        win.destroy()

    ttk.Button(win, text="Guardar", command=guardar).grid(row=row+2, column=1, pady=20)

# ========== GUI ==========


root = tk.Tk()
root.title(STRINGS["title"])
root.geometry("700x760")
root.minsize(700, 800)


# Variáveis globais para imagens
bg_photo = None
logo_photo = None


def load_background():
    global bg_photo
    bg_image_path = config["ASSET_PATHS"]["background"]
    if validar_arquivo(bg_image_path, "Imagem de fundo"):
        bg_image = Image.open(bg_image_path)
        bg_photo = ImageTk.PhotoImage(bg_image)
        background_label = tk.Label(root, image=bg_photo)
        background_label.image = bg_photo
        background_label.place(relwidth=1, relheight=1)
        background_label.lower()  # Isto envia o fundo para trás dos botões


def load_logo():
    global logo_photo
    logo_path = config["ASSET_PATHS"]["logo"]
    if validar_arquivo(logo_path, "Logo"):
        logo_img = Image.open(logo_path).resize((180, 180))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo_photo, bg="#ffffff")
        logo_label.image = logo_photo
        logo_label.grid(row=0, column=0, columnspan=3, pady=10)

# ========== Estilização ==========


style = ttk.Style()
style.theme_use("default")
style.configure("TButton", font=("Arial", 10), padding=(1, 1), background="#d9eaff", foreground="black", borderwidth=2)
style.map("TButton", background=[("active", "#b3d1ff")], foreground=[("active", "black")])
style.configure("Title.TLabel", font=("Arial", 12, "bold"), background="#ffffff")
style.configure("Danger.TButton", foreground="white", background="#e57373")
style.map("Danger.TButton", background=[("active", "#c62828")])

# ========== Barra de status ==========
status_texto = tk.StringVar()


def atualizar_status(msg: str):
    status_texto.set(f"{msg} | {datetime.now():%d/%m/%Y %H:%M}")


atualizar_status(STRINGS["status_ready"])
status_bar = tk.Label(root, textvariable=status_texto, bd=1, relief="sunken", anchor="w", font=("Arial", 9), bg="#eeeeee")
status_bar.grid(row=99, column=0, columnspan=3, sticky="we")

# ========== Tooltips ==========


def add_tooltip(widget, text):
    tooltip = tk.Toplevel(widget, bg="#ffffe0", padx=1, pady=1)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9))
    label.pack()

    def show_tip(event):
        tooltip.geometry(f"+{event.x_root+20}+{event.y_root+10}")
        tooltip.deiconify()

    def hide_tip(event):
        tooltip.withdraw()
    widget.bind("<Enter>", show_tip)
    widget.bind("<Leave>", hide_tip)

# ========== Layout principal (grid) ==========


main_frame = tk.Frame(root, bg="#ffffff", width=400)
main_frame.grid(row=1, column=0, pady=10)

# INTERFACES
ttk.Label(main_frame, text=STRINGS["interfaces"], style="Title.TLabel").grid(row=0, column=0, pady=5, sticky="w")
btn_cli = ttk.Button(main_frame, text=STRINGS["cli"], width=32, command=run_cli)
btn_cli.grid(row=1, column=0, pady=0, sticky="ew")
add_tooltip(btn_cli, STRINGS["tooltip_cli"])
root.bind_all('<Alt-c>', run_cli)

btn_gui = ttk.Button(main_frame, text=STRINGS["gui_local"], width=32, command=run_llm_local_gui)
btn_gui.grid(row=2, column=0, pady=2, sticky="ew")
add_tooltip(btn_gui, STRINGS["tooltip_gui"])

btn_discord = ttk.Button(main_frame, text=STRINGS["discord"], width=32, command=run_discord)
btn_discord.grid(row=3, column=0, pady=2, sticky="ew")
add_tooltip(btn_discord, STRINGS["tooltip_discord"])

# PROCESSAMENTO
ttk.Label(main_frame, text=STRINGS["processing"], style="Title.TLabel").grid(row=4, column=0, pady=(20, 5), sticky="ew")

btn_lote = ttk.Button(main_frame, text="Teste em Lote", width=32, command=lambda: executar_script("test_lote", "Teste em Lote"))
btn_lote.grid(row=5, column=0, pady=2, sticky="ew")
add_tooltip(btn_lote, "Executa um conjunto fixo de perguntas para testes rápidos")

btn_rag = ttk.Button(main_frame, text=STRINGS["rag"], width=32, command=abrir_rag_library_manager)
btn_rag.grid(row=6, column=0, pady=2, sticky="ew")
add_tooltip(btn_rag, STRINGS["tooltip_rag"])

btn_test = ttk.Button(main_frame, text=STRINGS["test"], width=32, command=run_test_request)
btn_test.grid(row=7, column=0, pady=2, sticky="ew")
add_tooltip(btn_test, STRINGS["tooltip_test"])

btn_metrics = ttk.Button(main_frame, text=STRINGS["metrics"], width=32, command=run_metrics)
btn_metrics.grid(row=8, column=0, pady=2, sticky="ew")
add_tooltip(btn_metrics, STRINGS["tooltip_metrics"])

# FICHEIROS
ttk.Label(main_frame, text=STRINGS["files"], style="Title.TLabel").grid(row=9, column=0, pady=12, sticky="ew")

btn_json = ttk.Button(main_frame, text=STRINGS["open_json"], width=32, command=open_respostas_json)
btn_json.grid(row=10, column=0, pady=2, sticky="ew")
add_tooltip(btn_json, STRINGS["tooltip_json"])

btn_csv = ttk.Button(main_frame, text=STRINGS["open_csv"], width=32, command=open_csv_comparativo)
btn_csv.grid(row=11, column=0, pady=2, sticky="ew")
add_tooltip(btn_csv, STRINGS["tooltip_csv"])

btn_log = ttk.Button(main_frame, text=STRINGS["open_log"], width=32, command=open_log)
btn_log.grid(row=12, column=0, pady=2, sticky="ew")
add_tooltip(btn_log, STRINGS["tooltip_log"])

btn_config = ttk.Button(main_frame, text=STRINGS["config"], width=32, command=open_config)
btn_config.grid(row=13, column=0, pady=8, sticky="ew")
add_tooltip(btn_config, STRINGS["tooltip_config"])

btn_ajuda = ttk.Button(main_frame, text="Ajuda / Sobre", width=32, command=abrir_ajuda)
btn_ajuda.grid(row=14, column=0, pady=8, sticky="ew")
add_tooltip(btn_ajuda, "Informações sobre o projeto e documentação.")

btn_exit = ttk.Button(main_frame, text=STRINGS["exit"], width=32, command=lambda: on_exit(), style="Danger.TButton")
btn_exit.grid(row=15, column=0, pady=20, sticky="ew")
add_tooltip(btn_exit, STRINGS["tooltip_exit"])


# ========== Função de fecho seguro ==========


def on_exit():
    if messagebox.askokcancel(STRINGS["exit"], STRINGS["confirm_exit"]):
        root.destroy()


root.protocol("WM_DELETE_WINDOW", on_exit)

# ========== Imagens ==========
load_logo()
load_background()


# ========== Layout expandido ==========
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
main_frame.columnconfigure(0, weight=1)

# ========== Executar aplicação ==========
if __name__ == "__main__":
    salvar_log("Painel iniciado.")
    root.mainloop()
