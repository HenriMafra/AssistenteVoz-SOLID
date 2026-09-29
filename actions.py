"""Módulo de fachada (Façade) retrocompatível para actions.py.

Delega chamadas para a nova arquitetura orientada a SOLID (actions/ e services/).
Permite que scripts legados e testes continuem funcionando sem alterações.
"""
from core.models import ResultadoAcao, ActionResult
from actions.app import APP_MAP, abrir_aplicativo
from actions.browser import abrir_navegador
from actions.cmd import executar_cmd
from actions.dispatcher import executar_acao_estruturada
from services.history_logger import registrar_transcricao

__all__ = [
    "APP_MAP",
    "ResultadoAcao",
    "ActionResult",
    "abrir_navegador",
    "executar_cmd",
    "abrir_aplicativo",
    "registrar_transcricao",
    "executar_acao_estruturada",
]
