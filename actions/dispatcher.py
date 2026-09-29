"""Despachante de Ações implementando o Open/Closed Principle (OCP).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  No projeto original (actions.py linhas 95-155), a função `executar_acao_estruturada`
  possuía um bloco condicional monolítico:
  `if acao == "abrir_navegador": ... elif acao == "executar_cmd": ... elif acao == "abrir_aplicativo": ...`

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação Crítica do Princípio Aberto/Fechado (OCP): Toda vez que o sistema precisava
     de uma nova ação (ex: ajustar volume, tirar screenshot, silenciar mic), era
     OBRIGATÓRIO abrir o arquivo `actions.py` e modificar diretamente a função central.
  2. Alto risco de regressão: Modificar código funcional e testado para adicionar novos
     recursos gera risco constante de introduzir bugs em funcionalidades antigas.
  3. Acoplamento de regras: A função acumulava lógicas específicas de cada comando
     (inclusive parsing de texto da transcrição na linha 129).

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Implementa o padrão Command / Strategy com a classe `ActionDispatcher`.
  O despachante agora está FECHADO para modificação e ABERTO para extensão.
  Novos comandos são adicionados simplesmente criando uma nova classe herdando de
  `BaseActionHandler` e chamando `dispatcher.registrar_handler(NovoHandler())`.
================================================================================
"""
from typing import Any
from core.interfaces import IActionHandler
from core.models import ActionResult, IntentResult
from .browser import BrowserActionHandler
from .cmd import CmdActionHandler
from .app import AppLauncherHandler


class ActionDispatcher:
    """Roteia e executa intenções baseando-se em handlers registrados (Strategy / Command - OCP)."""

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
