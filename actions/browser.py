"""Handler responsável exclusivamente por abrir URLs ou realizar pesquisas no navegador."""
import urllib.parse
import webbrowser
from typing import Any
from core.models import ActionResult, IntentResult
from .base import BaseActionHandler


def abrir_navegador(query_ou_url: str) -> str:
    """Abre URL ou pesquisa no Google no navegador padrão do sistema."""
    alvo = query_ou_url.strip()
    if alvo.startswith(("http://", "https://")):
        url = alvo
    else:
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(alvo)}"
    webbrowser.open(url)
    return url


import sys


class BrowserActionHandler(BaseActionHandler):
    """Executa ações de navegação web (SRP)."""

    @property
    def nome_acao(self) -> str:
        return "abrir_navegador"

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        query = (parametros.get("query") or parametros.get("url") or "").strip()
        if not query:
            return ActionResult(
                status="Nenhum termo ou URL fornecido para o navegador.",
                saida="Parâmetro 'query' ausente.",
                acao=self.nome_acao,
                success=False
            )

        mod = sys.modules.get("actions")
        if mod and hasattr(mod, "abrir_navegador") and mod.abrir_navegador is not self.executar:
            url_final = mod.abrir_navegador(query)
        else:
            url_final = abrir_navegador(query)

        return ActionResult(
            status=f"Navegador aberto com: '{query}'",
            saida=f"Pesquisa aberta no navegador:\n{url_final}",
            acao=self.nome_acao,
            success=True
        )
