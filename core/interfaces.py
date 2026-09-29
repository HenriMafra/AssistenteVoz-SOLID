"""Contratos e interfaces abstratas do sistema seguindo ISP (Interface Segregation Principle).

Cada interface possui um propósito estrito e coeso, evitando que clientes dependam
de métodos ou comportamentos desnecessários.
"""
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable
from .models import ActionResult, IntentResult


@runtime_checkable
class IAudioRecorder(Protocol):
    """Contrato exclusivo para dispositivos de captura de áudio."""

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
    """Contrato exclusivo para serviços de inteligência artificial de transcrição e intenção."""

    def processar_audio(self, audio_bytes: bytes) -> IntentResult:
        """Envia bytes de áudio para transcrição e interpretação."""
        ...

    def processar_texto(self, texto: str) -> IntentResult:
        """Processa comando em texto direto para interpretação de intenção."""
        ...


@runtime_checkable
class IActionHandler(Protocol):
    """Contrato para manipuladores de ações no sistema operacional (Command/Strategy Pattern)."""

    @property
    def nome_acao(self) -> str:
        """Identificador da ação retornado pela IA (ex: 'abrir_navegador')."""
        ...

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        """Executa a ação correspondente no sistema operacional."""
        ...


@runtime_checkable
class IHistoryLogger(Protocol):
    """Contrato para persistência e auditoria de histórico de comandos."""

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
