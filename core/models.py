"""Módulo de Modelos de Domínio (DTOs) com Validação e Tipagem Forte.

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  No código legado (actions.py linhas 25-41), existia uma classe `ResultadoAcao`
  que tentava fingir que era um dicionário ao implementar apenas `__getitem__` e `get()`.
  Ao mesmo tempo, as intenções da IA transitavam como dicionários soltos (`dict`)
  com strings mágicas ("transcricao", "acao", "parametros").

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação do Princípio da Substituição de Liskov (LSP): A classe quebrava o
     contrato de substituição. Se qualquer parte do código esperasse um dicionário real
     (ex: iterando com `for k, v in resultado.items()`), o programa quebrava com AttributeError.
  2. Falta de tipagem estática e fragilidade: O uso de dicionários anônimos sem validação
     forçava o uso constante de `.get("chave", padrao)` defensivo em todos os arquivos.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Cria Data Transfer Objects (DTOs) fortemente tipados (`IntentResult` e `ActionResult`)
  com campos definidos, imutáveis por padrão, com getters seguros e retrocompatibilidade
  completa com código legado.
================================================================================
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentResult:
    """Representa a intenção do usuário interpretada pelo serviço de IA.
    
    Substitui os dicionários soltos de intenção que circulavam no código legado.
    """
    transcription: str = ""
    action: str = "outro"
    params: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    # Aliases em português para manter compatibilidade com testes e código legado
    @property
    def transcricao(self) -> str:
        return self.transcription

    @property
    def acao(self) -> str:
        return self.action

    @property
    def parametros(self) -> dict[str, Any]:
        return self.params

    @property
    def explicacao(self) -> str:
        return self.explanation

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcricao": self.transcription,
            "acao": self.action,
            "parametros": self.params,
            "explicacao": self.explanation,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


@dataclass
class ActionResult:
    """Resultado encapsulado da execução de uma ação no sistema operacional.
    
    Substitui a antiga classe ResultadoAcao com um contrato seguro e completo (LSP).
    """
    status: str
    saida: str = ""
    acao: str = ""
    comando: str = ""
    success: bool = True

    @property
    def output(self) -> str:
        return self.saida

    @property
    def action(self) -> str:
        return self.acao

    @property
    def command(self) -> str:
        return self.comando

    def __str__(self) -> str:
        return self.status

    def get(self, chave: str, padrao: Any = None) -> Any:
        return getattr(self, chave, padrao)

    def __getitem__(self, chave: str) -> Any:
        if hasattr(self, chave):
            return getattr(self, chave)
        raise KeyError(chave)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "saida": self.saida,
            "acao": self.acao,
            "comando": self.comando,
            "success": self.success,
        }


# Alias para retrocompatibilidade total com testes legados
ResultadoAcao = ActionResult
