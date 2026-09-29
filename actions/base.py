"""Classe base e helpers para Handlers de Ações."""
from abc import ABC, abstractmethod
from typing import Any
from core.interfaces import IActionHandler
from core.models import ActionResult, IntentResult


class BaseActionHandler(IActionHandler, ABC):
    """Classe base que fornece comportamento padrão e implementação de IActionHandler."""

    @property
    @abstractmethod
    def nome_acao(self) -> str:
        """Nome único da ação."""
        pass

    @abstractmethod
    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        """Execução concreta da ação."""
        pass
