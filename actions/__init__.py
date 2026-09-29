"""Módulo de Ações e Execuções Locais do Windows."""
from core.models import ActionResult, ResultadoAcao
from .base import BaseActionHandler
from .browser import BrowserActionHandler, abrir_navegador
from .cmd import CmdActionHandler, executar_cmd
from .app import AppLauncherHandler, abrir_aplicativo, APP_MAP
from .dispatcher import ActionDispatcher, executar_acao_estruturada

from services.history_logger import registrar_transcricao

__all__ = [
    "ActionResult",
    "ResultadoAcao",
    "BaseActionHandler",
    "BrowserActionHandler",
    "abrir_navegador",
    "CmdActionHandler",
    "executar_cmd",
    "AppLauncherHandler",
    "abrir_aplicativo",
    "APP_MAP",
    "ActionDispatcher",
    "executar_acao_estruturada",
    "registrar_transcricao",
]
