"""Modelos de dados (DTOs) com validação e tipagem forte."""
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class IntentResult:
    """Representa a intenção do usuário interpretada pelo serviço de IA."""
    transcription: str = ""
    action: str = "outro"
    params: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    # Aliases em português para interoperabilidade
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
    """Resultado encapsulado da execução de uma ação no sistema operacional."""
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


# Alias para retrocompatibilidade
ResultadoAcao = ActionResult
