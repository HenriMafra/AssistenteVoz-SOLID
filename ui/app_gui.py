"""Interface Gráfica Tkinter desacoplada e aderente aos princípios SOLID (DIP e SRP).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  No projeto original (AssistenteVoz/app_gui.py), esta classe era uma clássica
  "God Class" (ou God Object) com mais de 730 linhas. Ela acumulava 8 responsabilidades:
  1. Criação de componentes visuais Tkinter;
  2. Desenho procedural de ondas no Canvas;
  3. Temporização e cronômetro de gravação;
  4. Gerenciamento manual de threads com `threading.Thread`;
  5. Instanciação física do microfone (`self.gravador = GravadorAudio(samplerate=16000)`);
  6. Chamada direta de rede da API do Google Gemini (`resultado = processar_audio(wav_bytes)`);
  7. Invocação direta de comandos e processos locais no SO (`status = executar_acao_estruturada()`);
  8. Lançador de arquivos externos do SO (`os.startfile` e Notepad).

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação Crítica de Responsabilidade Única (SRP): A interface gráfica tinha múltiplos
     motivos para mudar. Se o endpoint do Gemini mudasse, a GUI quebrava. Se a captura de
     áudio mudasse, a GUI quebrava. Se as ações no Windows mudassem, a GUI quebrava.
  2. Violação Crítica de Inversão de Dependência (DIP): O módulo de mais alto nível
     (a camada de apresentação visual) estava fortemente acoplado a bibliotecas de
     baixo nível (`requests`, `subprocess`, `sounddevice`).
  3. Impossibilidade de testes unitários isolados: Qualquer teste na GUI precisava
     mockar a placa de som e os servidores da Google, tornando os testes lentos e frágeis.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  A classe AssistenteVozGUI foi convertida em uma "View" pura (padrão MVC/MVP).
  Ela não sabe o que é Gemini, não sabe como o som é gravado e não sabe como o CMD
  roda comandos. Toda a lógica de negócio é delegada ao `VoiceAssistantController`
  recebido por Injeção de Dependências no `__init__`.
================================================================================
"""
import os
import random
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Any

from core.models import ActionResult, IntentResult
from actions.app import abrir_aplicativo
from services.controller import VoiceAssistantController


class AssistenteVozGUI:
    """Interface Gráfica Moderna para o Assistente de Voz."""

    def __init__(self, root: tk.Tk, controller: VoiceAssistantController | None = None):
        self.root = root
        self.root.title("Assistente de Voz IA — Gemini Flash (SOLID)")

        # Injeção de dependência do controlador (DIP)
        # Substitui a instanciação acoplada antiga `self.gravador = GravadorAudio(...)`
        self.controller = controller or VoiceAssistantController()
        # Atalho de compatibilidade com testes unitários legados
        self.gravador = self.controller.recorder

        # Centralizar na tela com dimensões ideais
        self.largura = 570
        self.altura = 810
        self._centralizar_janela()
        self.root.minsize(520, 720)

        # Paleta de Cores Moderna (Slate & Obsidian Theme)
        self.cores = {
            "bg": "#0B0F19",
            "card": "#151D2E",
            "card_interno": "#0D1322",
            "borda": "#26334D",
            "borda_foco": "#38BDF8",
            "texto": "#F8FAFC",
            "texto_secundario": "#94A3B8",
            "azul": "#38BDF8",
            "azul_btn": "#2563EB",
            "azul_btn_hover": "#1D4ED8",
            "verde": "#34D399",
            "verde_bg": "#064E3B",
            "vermelho": "#F43F5E",
            "vermelho_hover": "#E11D48",
            "amarelo": "#FBBF24",
            "amarelo_bg": "#78350F",
            "cinza_btn": "#334155",
            "cinza_btn_hover": "#475569",
        }
        self.root.configure(bg=self.cores["bg"])

        self.esta_gravando = False
        self.processando = False
        self.cancelado = False
        self.segundos_gravacao = 0
        self.timer_id = None
        self.anim_id = None

        self._construir_interface()
        self._verificar_conexao()

    def _centralizar_janela(self):
        try:
            self.root.update_idletasks()
            sw = int(self.root.winfo_screenwidth())
            sh = int(self.root.winfo_screenheight())
            x = max(0, (sw - self.largura) // 2)
            y = max(0, (sh - self.altura) // 2 - 30)
            self.root.geometry(f"{self.largura}x{self.altura}+{x}+{y}")
        except Exception:
            self.root.geometry(f"{self.largura}x{self.altura}")

    def _construir_interface(self):
        # 1. HEADER
        header = tk.Frame(self.root, bg=self.cores["bg"])
        header.pack(fill="x", padx=24, pady=(18, 10))

        titulo_frame = tk.Frame(header, bg=self.cores["bg"])
        titulo_frame.pack(side="left")

        lbl_icone = tk.Label(
            titulo_frame,
            text="🎙️",
            font=("Segoe UI", 20),
            bg=self.cores["bg"],
            fg=self.cores["azul"]
        )
        lbl_icone.pack(side="left", padx=(0, 10))

        textos_titulo = tk.Frame(titulo_frame, bg=self.cores["bg"])
        textos_titulo.pack(side="left")

        lbl_titulo = tk.Label(
            textos_titulo,
            text="Assistente de Voz IA (SOLID)",
            font=("Segoe UI", 16, "bold"),
            fg=self.cores["texto"],
            bg=self.cores["bg"]
        )
        lbl_titulo.pack(anchor="w")

        lbl_sub = tk.Label(
            textos_titulo,
            text="Linguagem Natural para Ações no Windows",
            font=("Segoe UI", 9),
            fg=self.cores["texto_secundario"],
            bg=self.cores["bg"]
        )
        lbl_sub.pack(anchor="w")

        # Badge de Conexão
        self.badge_frame = tk.Frame(
            header,
            bg=self.cores["card"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1,
            padx=10,
            pady=4
        )
        self.badge_frame.pack(side="right", pady=5)

        self.lbl_status_badge = tk.Label(
            self.badge_frame,
            text="● Conectando...",
            font=("Segoe UI", 8, "bold"),
            fg=self.cores["amarelo"],
            bg=self.cores["card"]
        )
        self.lbl_status_badge.pack()

        # 2. CARD DO MICROFONE
        self.card_mic = tk.Frame(
            self.root,
            bg=self.cores["card"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.card_mic.pack(fill="x", padx=24, pady=8)

        self.lbl_instrucao = tk.Label(
            self.card_mic,
            text="Pronto para ouvir. Clique no botão e fale naturalmente.",
            font=("Segoe UI", 10, "bold"),
            fg=self.cores["texto"],
            bg=self.cores["card"]
        )
        self.lbl_instrucao.pack(pady=(16, 6))

        # Canvas de ondas sonoras
        self.canvas_ondas = tk.Canvas(
            self.card_mic,
            width=260,
            height=24,
            bg=self.cores["card"],
            highlightthickness=0
        )
        self.canvas_ondas.pack(pady=(0, 6))
        self._desenhar_ondas_repouso()

        # Botão Principal de Gravação
        self.btn_falar = tk.Button(
            self.card_mic,
            text="🎙️  CLIQUE PARA FALAR",
            font=("Segoe UI", 12, "bold"),
            fg="#FFFFFF",
            bg=self.cores["azul_btn"],
            activebackground=self.cores["azul_btn_hover"],
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=13,
            relief="flat",
            command=self._alternar_gravacao
        )
        self.btn_falar.pack(fill="x", padx=24, pady=4)
        self._aplicar_hover(self.btn_falar, self.cores["azul_btn"], self.cores["azul_btn_hover"])

        # Botões secundários
        botoes_acao_frame = tk.Frame(self.card_mic, bg=self.cores["card"])
        botoes_acao_frame.pack(fill="x", padx=24, pady=(8, 4))

        self.btn_cancelar = tk.Button(
            botoes_acao_frame,
            text="✕ Cancelar",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg=self.cores["vermelho"],
            activebackground=self.cores["vermelho_hover"],
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=7,
            state="disabled",
            relief="flat",
            command=self._cancelar_operacao
        )
        self.btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_tentar_novamente = tk.Button(
            botoes_acao_frame,
            text="↻ Tentar Novamente",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg=self.cores["cinza_btn"],
            activebackground=self.cores["cinza_btn_hover"],
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=7,
            relief="flat",
            command=self._tentar_novamente
        )
        self.btn_tentar_novamente.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Indicador de tempo e dicas
        self.lbl_cronometro = tk.Label(
            self.card_mic,
            text="Exemplos: 'abra o google e pesquise...', 'abra o cmd...', 'abra a calculadora'",
            font=("Segoe UI", 8, "italic"),
            fg=self.cores["texto_secundario"],
            bg=self.cores["card"]
        )
        self.lbl_cronometro.pack(pady=(6, 14))

        # 3. ENTRADA MANUAL POR TEXTO
        input_container = tk.Frame(self.root, bg=self.cores["bg"])
        input_container.pack(fill="x", padx=24, pady=(4, 8))

        self.entry_frame = tk.Frame(
            input_container,
            bg=self.cores["card"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.entry_frame.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.entry_comando = tk.Entry(
            self.entry_frame,
            font=("Segoe UI", 10),
            bg=self.cores["card"],
            fg=self.cores["texto"],
            insertbackground=self.cores["azul"],
            bd=0
        )
        self.entry_comando.pack(fill="x", padx=10, ipady=7)
        self.entry_comando.bind("<Return>", lambda event: self._enviar_texto())

        self.btn_enviar_texto = tk.Button(
            input_container,
            text="Enviar",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg=self.cores["cinza_btn"],
            activebackground=self.cores["cinza_btn_hover"],
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=6,
            relief="flat",
            command=self._enviar_texto
        )
        self.btn_enviar_texto.pack(side="right")
        self._aplicar_hover(self.btn_enviar_texto, self.cores["cinza_btn"], self.cores["cinza_btn_hover"])

        # 4. CARD DE DETALHES E EXECUÇÃO
        self.card_detalhes = tk.Frame(
            self.root,
            bg=self.cores["card"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.card_detalhes.pack(fill="both", expand=True, padx=24, pady=(4, 10))

        header_detalhes = tk.Frame(self.card_detalhes, bg=self.cores["card"])
        header_detalhes.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header_detalhes,
            text="RESPOSTA E EXECUÇÃO DA IA",
            font=("Segoe UI", 8, "bold"),
            fg=self.cores["texto_secundario"],
            bg=self.cores["card"]
        ).pack(side="left")

        # Container 1: Compreensão
        tk.Label(
            self.card_detalhes,
            text="🧠 O que foi compreendido pela IA:",
            font=("Segoe UI", 9, "bold"),
            fg=self.cores["azul"],
            bg=self.cores["card"]
        ).pack(anchor="w", padx=16, pady=(4, 2))

        self.box_comp = tk.Frame(
            self.card_detalhes,
            bg=self.cores["card_interno"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.box_comp.pack(fill="x", padx=16, pady=(0, 8))

        self.txt_compreendido = tk.Label(
            self.box_comp,
            text="Aguardando comando de voz ou texto...",
            font=("Segoe UI", 10),
            fg=self.cores["texto"],
            bg=self.cores["card_interno"],
            wraplength=480,
            justify="left",
            anchor="w",
            padx=12,
            pady=10
        )
        self.txt_compreendido.pack(fill="x")

        # Container 2: Execução
        tk.Label(
            self.card_detalhes,
            text="⚡ O que ela vai executar:",
            font=("Segoe UI", 9, "bold"),
            fg=self.cores["verde"],
            bg=self.cores["card"]
        ).pack(anchor="w", padx=16, pady=(2, 2))

        self.box_exec = tk.Frame(
            self.card_detalhes,
            bg=self.cores["card_interno"],
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.box_exec.pack(fill="x", padx=16, pady=(0, 10))

        self.txt_vai_executar = tk.Label(
            self.box_exec,
            text="Nenhuma ação em execução no momento.",
            font=("Segoe UI", 10),
            fg=self.cores["verde"],
            bg=self.cores["card_interno"],
            wraplength=480,
            justify="left",
            anchor="w",
            padx=12,
            pady=8
        )
        self.txt_vai_executar.pack(fill="x")

        # Container 3: Saída Real
        tk.Label(
            self.card_detalhes,
            text="📋 Resultado da Execução (Saída Real do Sistema / CMD):",
            font=("Segoe UI", 9, "bold"),
            fg=self.cores["amarelo"],
            bg=self.cores["card"]
        ).pack(anchor="w", padx=16, pady=(2, 2))

        self.box_saida = tk.Frame(
            self.card_detalhes,
            bg="#080C16",
            highlightbackground=self.cores["borda"],
            highlightthickness=1
        )
        self.box_saida.pack(fill="x", padx=16, pady=(0, 10))

        self.txt_saida_real = tk.Label(
            self.box_saida,
            text="Aguardando retorno do comando...",
            font=("Consolas", 9),
            fg="#E2E8F0",
            bg="#080C16",
            wraplength=480,
            justify="left",
            anchor="w",
            padx=12,
            pady=8
        )
        self.txt_saida_real.pack(fill="x")

        # Rodapé
        rodape = tk.Frame(self.card_detalhes, bg=self.cores["card"])
        rodape.pack(fill="x", padx=16, pady=(0, 10))

        btn_historico = tk.Button(
            rodape,
            text="📄 Abrir Histórico Completo (transcricao.md)",
            font=("Segoe UI", 8, "underline"),
            fg=self.cores["azul"],
            bg=self.cores["card"],
            activebackground=self.cores["card"],
            activeforeground=self.cores["texto"],
            bd=0,
            cursor="hand2",
            command=self._abrir_historico
        )
        btn_historico.pack(side="left")

    def _aplicar_hover(self, widget, cor_normal, cor_hover):
        widget.bind("<Enter>", lambda e: widget.config(bg=cor_hover) if str(widget["state"]) != "disabled" else None)
        widget.bind("<Leave>", lambda e: widget.config(bg=cor_normal) if str(widget["state"]) != "disabled" else None)

    def _desenhar_ondas_repouso(self):
        self.canvas_ondas.delete("all")
        w, h = 260, 24
        barras = 24
        largura_barra = 4
        espacamento = 6
        inicio_x = (w - (barras * (largura_barra + espacamento))) // 2
        for i in range(barras):
            x = inicio_x + i * (largura_barra + espacamento)
            self.canvas_ondas.create_line(
                x, h // 2 - 2, x, h // 2 + 2,
                fill=self.cores["cinza_btn"],
                width=largura_barra,
                capstyle="round"
            )

    def _animar_ondas_gravando(self):
        if not self.esta_gravando:
            self._desenhar_ondas_repouso()
            return

        self.canvas_ondas.delete("all")
        w, h = 260, 24
        barras = 24
        largura_barra = 4
        espacamento = 6
        inicio_x = (w - (barras * (largura_barra + espacamento))) // 2

        for i in range(barras):
            x = inicio_x + i * (largura_barra + espacamento)
            altura_onda = random.randint(3, 10)
            self.canvas_ondas.create_line(
                x, (h // 2) - altura_onda, x, (h // 2) + altura_onda,
                fill=self.cores["vermelho"],
                width=largura_barra,
                capstyle="round"
            )

        self.anim_id = self.root.after(120, self._animar_ondas_gravando)

    def _verificar_conexao(self):
        if self.controller.verificar_conexao():
            self.lbl_status_badge.config(
                text="● Conectado ao Gemini",
                fg=self.cores["verde"]
            )
            self.badge_frame.config(highlightbackground=self.cores["verde"])
        else:
            self.lbl_status_badge.config(
                text="❌ Chave Ausente (.env)",
                fg=self.cores["vermelho"]
            )
            self.badge_frame.config(highlightbackground=self.cores["vermelho"])

    def _alternar_gravacao(self):
        if not self.esta_gravando:
            self._iniciar_gravacao()
        else:
            self._finalizar_e_enviar()

    def _iniciar_gravacao(self):
        if self.processando:
            return

        try:
            self.cancelado = False
            self.controller.iniciar_gravacao()
            self.esta_gravando = True
            self.segundos_gravacao = 0

            self.btn_falar.config(
                text="⏹️  ENVIAR ÁUDIO AGORA",
                bg=self.cores["vermelho"],
                activebackground=self.cores["vermelho_hover"],
                state="normal"
            )
            self.lbl_instrucao.config(
                text="🔴 Ouvindo... Fale agora o que deseja que o PC faça.",
                fg=self.cores["vermelho"]
            )
            self.btn_cancelar.config(state="normal")
            self.btn_tentar_novamente.config(state="normal")

            self._animar_ondas_gravando()
            self._atualizar_cronometro()

        except Exception as e:
            messagebox.showerror("Erro de Microfone", f"Não foi possível iniciar o microfone:\n{e}")
            self._resetar_estado_pronto()

    def _atualizar_cronometro(self):
        if self.esta_gravando:
            self.segundos_gravacao += 1
            self.lbl_cronometro.config(
                text=f"Gravando: {self.segundos_gravacao}s de 12s máx  •  Clique em 'Cancelar' para desistir"
            )
            if self.segundos_gravacao >= 12:
                self.lbl_cronometro.config(
                    text="Tempo limite atingido. Enviando áudio..."
                )
                self._finalizar_e_enviar()
                return

            self.timer_id = self.root.after(1000, self._atualizar_cronometro)

    def _finalizar_e_enviar(self):
        if not self.esta_gravando:
            return

        self.esta_gravando = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        self._desenhar_ondas_repouso()
        self.processando = True
        self.cancelado = False

        self.btn_falar.config(
            text="⏳  PROCESSANDO COM IA...",
            bg=self.cores["amarelo"],
            activebackground=self.cores["amarelo"],
            state="disabled"
        )
        self.lbl_instrucao.config(
            text="Enviando áudio para o Gemini Flash interpretar...",
            fg=self.cores["amarelo"]
        )
        self.btn_cancelar.config(state="normal")
        self.btn_tentar_novamente.config(state="normal")

        threading.Thread(target=self._worker_processar_audio, daemon=True).start()

    def _worker_processar_audio(self):
        """Thread trabalhadora para processamento de voz.
        
        NO CÓDIGO LEGADO (app_gui.py linhas 548-562):
        Aqui a GUI chamava `resultado = processar_audio(wav_bytes)` e em seguida
        `status = executar_acao_estruturada(resultado)`.
        Isso era CRÍTICO porque a interface gráfica executava requisições de rede
        e processos do Windows diretamente dentro de si mesma.
        
        AGORA:
        A interface apenas avisa o Controller de aplicação e recebe o resultado
        pronto e formatado de forma limpa e assíncrona.
        """
        try:
            intent, status = self.controller.finalizar_e_processar_voz()
            if self.cancelado:
                return
            self.root.after(0, self._atualizar_sucesso, intent, status)
        except Exception as e:
            if not self.cancelado:
                self.root.after(0, self._atualizar_erro, str(e))

    def _cancelar_operacao(self):
        """Aborta a operação imediatamente."""
        self.cancelado = True

        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        if self.anim_id:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None

        try:
            self.controller.cancelar_gravacao()
        except Exception:
            pass

        self._desenhar_ondas_repouso()
        self._resetar_estado_pronto()
        self.lbl_instrucao.config(
            text="Operação cancelada pelo usuário.",
            fg=self.cores["texto_secundario"]
        )
        self.lbl_cronometro.config(
            text="Pronto para uma nova tentativa. Clique no microfone."
        )

    def _tentar_novamente(self):
        """Limpa e reinicia nova gravação imediatamente."""
        self._cancelar_operacao()
        self.txt_compreendido.config(text="Aguardando novo comando...")
        self.txt_vai_executar.config(text="Aguardando...")
        self.txt_saida_real.config(text="Aguardando retorno do comando...")
        self.root.after(120, self._iniciar_gravacao)

    def _enviar_texto(self):
        if self.processando or self.esta_gravando:
            return

        comando = self.entry_comando.get().strip()
        if not comando:
            return

        self.entry_comando.delete(0, "end")
        self.processando = True
        self.cancelado = False

        self.btn_falar.config(state="disabled")
        self.btn_cancelar.config(state="normal")
        self.btn_tentar_novamente.config(state="normal")
        self.lbl_instrucao.config(
            text="Processando comando digitado com IA...",
            fg=self.cores["amarelo"]
        )

        threading.Thread(target=self._worker_processar_texto, args=(comando,), daemon=True).start()

    def _worker_processar_texto(self, comando: str):
        """Thread trabalhadora para processamento de texto.
        
        NO CÓDIGO LEGADO (app_gui.py linhas 624-636):
        A interface gráfica invocava diretamente `processar_texto` e `executar_acao_estruturada`.
        
        AGORA:
        Delega a interpretação e execução ao VoiceAssistantController.
        """
        try:
            intent, status = self.controller.processar_comando_texto(comando)
            if self.cancelado:
                return
            self.root.after(0, self._atualizar_sucesso, intent, status)
        except Exception as e:
            if not self.cancelado:
                self.root.after(0, self._atualizar_erro, str(e))

    def _atualizar_sucesso(self, resultado: Any, status: Any):
        self._resetar_estado_pronto()

        if isinstance(resultado, IntentResult):
            transcricao = resultado.transcription
            explicacao = resultado.explanation
            acao = resultado.action.upper()
            params = resultado.params
        elif isinstance(resultado, dict):
            transcricao = resultado.get("transcricao", "")
            explicacao = resultado.get("explicacao", "")
            acao = str(resultado.get("acao", "outro")).upper()
            params = resultado.get("parametros", {})
        else:
            transcricao = str(resultado)
            explicacao = ""
            acao = "OUTRO"
            params = {}

        # 1. O que foi compreendido
        detalhes_compreensao = (
            f"Fala Detectada: \"{transcricao}\"\n"
            f"Intenção: {explicacao}"
        )
        self.txt_compreendido.config(text=detalhes_compreensao)

        # 2. O que ela vai executar
        status_str = getattr(status, "status", str(status))
        detalhes_execucao = (
            f"Ação: [{acao}]\n"
            f"Parâmetros: {params}\n"
            f"Status: ✔ {status_str}"
        )
        self.txt_vai_executar.config(text=detalhes_execucao)

        # 3. Resultado real
        saida_real = getattr(status, "saida", "")
        if not saida_real and isinstance(status, dict):
            saida_real = status.get("saida", "")
        if not saida_real:
            saida_real = status_str
        self.txt_saida_real.config(text=saida_real)

        self.lbl_instrucao.config(
            text="✔ Ação executada com sucesso no computador!",
            fg=self.cores["verde"]
        )
        self.lbl_cronometro.config(
            text="Clique novamente para falar outro comando."
        )

    def _atualizar_erro(self, msg_erro: str):
        self._resetar_estado_pronto()

        self.txt_compreendido.config(
            text=f"Não foi possível compreender o áudio ou texto.\nDetalhe: {msg_erro}"
        )
        self.txt_vai_executar.config(text="Nenhuma ação executada.")
        self.txt_saida_real.config(text=f"Falha na execução: {msg_erro}")

        self.lbl_instrucao.config(
            text="✕ Ocorreu um problema no processamento.",
            fg=self.cores["vermelho"]
        )
        self.lbl_cronometro.config(
            text="Dica: Clique em 'Tentar Novamente' e fale próximo ao microfone."
        )

    def _resetar_estado_pronto(self):
        self.esta_gravando = False
        self.processando = False

        self.btn_falar.config(
            text="🎙️  CLIQUE PARA FALAR",
            bg=self.cores["azul_btn"],
            activebackground=self.cores["azul_btn_hover"],
            state="normal"
        )
        self.btn_cancelar.config(state="disabled")
        self.btn_tentar_novamente.config(state="normal")
        self.lbl_instrucao.config(
            text="Pronto para ouvir. Clique no botão e fale naturalmente.",
            fg=self.cores["texto"]
        )

    def _abrir_historico(self):
        caminho_md = Path("transcricao.md")
        if not caminho_md.exists():
            messagebox.showinfo("Histórico", "Nenhum histórico foi gerado ainda.")
            return

        try:
            os.startfile(caminho_md)
        except Exception:
            abrir_aplicativo(f"notepad {caminho_md}")


def iniciar_gui():
    root = tk.Tk()
    app = AssistenteVozGUI(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_gui()
