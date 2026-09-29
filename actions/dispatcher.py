"""Despachante de Ações implementando o Open/Closed Principle (OCP).

Permite estender o sistema com novas ações sem nunca precisar modificar
o despachante ou as ações existentes.
"""
from typing import Any
from core.interfaces import IActionHandler
from core.models import ActionResult, IntentResult
from .browser import BrowserActionHandler
from .cmd import CmdActionHandler
from .app import AppLauncherHandler


class ActionDispatcher:
    """Roteia e executa intenções baseando-se em handlers registrados (Strategy / Command)."""

    def __init__(self, handlers: list[IActionHandler] | None = None):
        self._handlers: dict[str, IActionHandler] = {}
        if handlers:
            for h in handlers:
                self.registrar_handler(h)
        else:
            # Registra os handlers padrão do sistema
            self.registrar_handler(BrowserActionHandler())
            self.registrar_handler(CmdActionHandler())
            self.registrar_handler(AppLauncherHandler())

    def registrar_handler(self, handler: IActionHandler) -> "ActionDispatcher":
        """Registra um novo manipulador de ação (Aberto para Extensão)."""
        self._handlers[handler.nome_acao] = handler
        return self

    def remover_handler(self, nome_acao: str) -> None:
        """Remove um manipulador registrado."""
        self._handlers.pop(nome_acao, None)

    def listar_acoes(self) -> list[str]:
        """Retorna lista com nomes de todas as ações suportadas."""
        return list(self._handlers.keys())

    def despachar(self, intent: IntentResult | dict[str, Any]) -> ActionResult:
        """Executa a ação correspondente à intenção fornecida."""
        if isinstance(intent, dict):
            intent_obj = IntentResult(
                transcription=intent.get("transcricao", ""),
                action=intent.get("acao", "outro"),
                params=intent.get("parametros", {}),
                explanation=intent.get("explicacao", "")
            )
        else:
            intent_obj = intent

        handler = self._handlers.get(intent_obj.action)
        if not handler:
            return ActionResult(
                status="Nenhuma ação local correspondente executada.",
                saida="Comando identificado como pergunta ou solicitação não operacional.",
                acao="outro",
                success=True
            )

        return handler.executar(intent_obj.params, contexto=intent_obj)


# Instância global padrão do despachante
_instancia_dispatcher = ActionDispatcher()


def executar_acao_estruturada(dados: dict[str, Any] | IntentResult) -> ActionResult:
    """Função compatível com a interface legada, delegando para o ActionDispatcher."""
    return _instancia_dispatcher.despachar(dados)
