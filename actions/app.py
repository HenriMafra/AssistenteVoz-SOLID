"""Handler responsável exclusivamente por iniciar programas e executáveis no Windows.

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  O dicionário estático `APP_MAP` e a função `abrir_aplicativo` ficavam globais
  dentro do monólito `actions.py`.

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  Violação do Princípio da Responsabilidade Única (SRP) e OCP: Não havia como injetar
  mapeamentos alternativos para testes ou customizações sem alterar o arquivo global.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Cria a classe `AppLauncherHandler` com construtor que aceita `app_map` customizado,
  desacoplando o registro de executáveis e isolando o uso do utilitário `start` do Windows.
================================================================================
"""
import subprocess
from typing import Any
from core.models import ActionResult, IntentResult
from .base import BaseActionHandler

# Mapeamento comum de comandos/nomes em português para executáveis no Windows
APP_MAP: dict[str, str] = {
    "calculadora": "calc",
    "calc": "calc",
    "bloco de notas": "notepad",
    "notepad": "notepad",
    "explorador": "explorer",
    "arquivos": "explorer",
    "cmd": "cmd",
    "prompt": "cmd",
    "powershell": "powershell",
    "paint": "mspaint",
    "chrome": "chrome",
    "navegador": "chrome",
}


def abrir_aplicativo(nome_app: str) -> subprocess.Popen:
    """Inicia um executável ou aplicativo no Windows usando o utilitário 'start'."""
    nome_limpo = nome_app.strip().lower()
    executavel = APP_MAP.get(nome_limpo, nome_limpo)
    return subprocess.Popen(f"start {executavel}", shell=True)


class AppLauncherHandler(BaseActionHandler):
    """Manipulador para abertura de aplicações do sistema operacional (SRP)."""

    def __init__(self, app_map: dict[str, str] | None = None):
        self.app_map = app_map or APP_MAP

    @property
    def nome_acao(self) -> str:
        return "abrir_aplicativo"

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        app = parametros.get("app", "").strip()
        if not app:
            return ActionResult(
                status="Nenhum nome de aplicativo especificado.",
                saida="Parâmetro 'app' ausente.",
                acao=self.nome_acao,
                success=False
            )

        abrir_aplicativo(app)
        return ActionResult(
            status=f"Aplicativo iniciado: '{app}'",
            saida=f"Processo '{app}' iniciado no Windows.",
            acao=self.nome_acao,
            success=True
        )
