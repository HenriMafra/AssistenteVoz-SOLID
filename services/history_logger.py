"""Serviço dedicado à persistência e auditoria de histórico de comandos (SRP).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  A função `registrar_transcricao()` estava declarada dentro de `actions.py` (linhas 75-93)
  e era chamada de dentro de `gemini_service.py` (linhas 200 e 240).

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação de Responsabilidade Única (SRP): Misturava operações de I/O em arquivo
     Markdown com automação do sistema operacional (abrir janelas e CMD).
  2. Dependência imprópria e acoplamento: O serviço de IA na nuvem dependia do arquivo
     de automação do SO local apenas para poder salvar um log em disco.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Isola a responsabilidade de formatação e escrita em disco na classe
  `MarkdownHistoryLogger`, implementando o contrato `IHistoryLogger`.
  Se amanhã o histórico precisar ser gravado em SQLite, JSON ou na nuvem,
  nenhuma linha de `actions` ou de `gemini_service` precisa ser tocada.
================================================================================
"""
from datetime import datetime
from pathlib import Path
from typing import Any
from core.interfaces import IHistoryLogger
from core.models import ActionResult, IntentResult


def registrar_transcricao(
    texto: str,
    acao: str,
    detalhes: dict[str, Any],
    arquivo: str = "transcricao.md"
) -> None:
    """Função utilitária para registrar histórico em arquivo Markdown."""
    caminho = Path(arquivo)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entrada = (
        f"### [{agora}]\n"
        f"- **Transcrição**: {texto}\n"
        f"- **Ação**: `{acao}`\n"
        f"- **Detalhes**: `{detalhes}`\n\n"
    )

    if not caminho.exists():
        cabecalho = "# Histórico de Transcrições e Comandos de Voz\n\n"
        caminho.write_text(cabecalho + entrada, encoding="utf-8")
    else:
        with caminho.open("a", encoding="utf-8") as f:
            f.write(entrada)


class MarkdownHistoryLogger(IHistoryLogger):
    """Implementação de logger persistente em arquivo Markdown (SRP / DIP)."""

    def __init__(self, arquivo_destino: str = "transcricao.md"):
        self.arquivo_destino = arquivo_destino

    def registrar(self, texto: str, acao: str, detalhes: dict[str, Any]) -> None:
        registrar_transcricao(
            texto=texto,
            acao=acao,
            detalhes=detalhes,
            arquivo=self.arquivo_destino
        )

    def registrar_execucao(self, intent: IntentResult, result: ActionResult) -> None:
        """Registra a tupla completa (intenção + resultado de execução)."""
        detalhes = dict(intent.params)
        detalhes["resultado_status"] = result.status
        self.registrar(
            texto=intent.transcription,
            acao=intent.action,
            detalhes=detalhes
        )
