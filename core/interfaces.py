"""Contratos e interfaces abstratas do sistema seguindo ISP (Interface Segregation Principle).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  Não existia nenhum arquivo de contratos ou interfaces formais no projeto original.
  Componentes de alto nível dependiam diretamente de classes e funções de baixo nível:
  - app_gui.py dependia diretamente de GravadorAudio, processar_audio e executar_acao_estruturada.
  - gemini_service.py dependia diretamente de registrar_transcricao de actions.py.

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação do Princípio da Segregação de Interfaces (ISP): Como não havia separação,
     qualquer consumidor que precisasse apenas processar áudio era obrigado a carregar
     dependências de subprocess, tkinter, sounddevice e filesystem juntos.
  2. Violação do Princípio da Inversão de Dependência (DIP): Módulos de alto nível
     estavam acoplados aos detalhes de implementação (bibliotecas third-party). Era
     impossível substituir o Gemini por Grok ou OpenAI sem refazer a interface gráfica.
  3. Dificuldade severa de testes: Testes unitários exigiam interceptar chamadas globais
     de bibliotecas em C (`sounddevice`, `webbrowser`, `requests`), tornando a suíte frágil.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Define contratos estritos e atômicos via `typing.Protocol`. Cada interface atende a
  um único propósito, permitindo substituir qualquer detalhe de implementação
  (ex: usar Grok em vez de Gemini ou PyAudio em vez de SoundDevice) sem alterar uma única linha
  da camada visual ou de aplicação.
================================================================================
"""
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable
from .models import ActionResult, IntentResult


@runtime_checkable
class IAudioRecorder(Protocol):
    """Contrato exclusivo para dispositivos de captura de áudio (ISP).
    
    Isola a responsabilidade de manipulação do hardware de som.
    No legado, essa lógica estava misturada dentro de gemini_service.py.
    """

    def iniciar(self) -> None:
        """Inicia a gravação de áudio do microfone."""
        ...

    def parar(self) -> bytes:
        """Encerra a gravação e retorna os bytes do áudio (formato WAV)."""
        ...

    def cancelar(self) -> None:
        """Cancela e descarta a gravação corrente sem gerar bytes."""
        ...

    def esta_gravando(self) -> bool:
        """Indica se a captura está em andamento."""
        ...


@runtime_checkable
class IAIService(Protocol):
    """Contrato exclusivo para serviços de inteligência artificial de transcrição e intenção (ISP/DIP).
    
    Permite trocar o Google Gemini pelo Grok, Claude ou OpenAI Whisper sem alterar a UI.
    """

    def processar_audio(self, audio_bytes: bytes) -> IntentResult:
        """Envia bytes de áudio para transcrição e interpretação."""
        ...

    def processar_texto(self, texto: str) -> IntentResult:
        """Processa comando em texto direto para interpretação de intenção."""
        ...


@runtime_checkable
class IActionHandler(Protocol):
    """Contrato para manipuladores de ações no sistema operacional (Command/Strategy Pattern).
    
    Permite que novas ações sejam criadas e registradas sem modificar o despachante (OCP).
    """

    @property
    def nome_acao(self) -> str:
        """Identificador da ação retornado pela IA (ex: 'abrir_navegador')."""
        ...

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        """Executa a ação correspondente no sistema operacional."""
        ...


@runtime_checkable
class IHistoryLogger(Protocol):
    """Contrato para persistência e auditoria de histórico de comandos (SRP/ISP).
    
    Desacopla a gravação de arquivo Markdown das chamadas de rede e do sistema operacional.
    """

    def registrar(self, texto: str, acao: str, detalhes: dict[str, Any]) -> None:
        """Grava uma entrada no histórico persistente."""
        ...


@runtime_checkable
class ISystemExecutor(Protocol):
    """Abstração para interações diretas com o Sistema Operacional."""

    def abrir_url(self, url: str) -> None:
        """Abre uma URL no navegador padrão."""
        ...

    def executar_processo(self, comando: str, shell: bool = True) -> Any:
        """Executa um processo no sistema operacional."""
        ...
