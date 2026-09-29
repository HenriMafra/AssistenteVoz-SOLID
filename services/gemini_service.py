"""Serviço de Inteligência Artificial com Google Gemini (SRP e DIP).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  No projeto original (gemini_service.py):
  1. Linha 13: `from actions import registrar_transcricao` (acoplamento impróprio).
  2. Linhas 200-204 e 239-243: As funções `processar_audio` e `processar_texto`
     gravavam silenciosamente em disco no arquivo `transcricao.md` a cada inferência.
  3. A lista de modelos `modelos = [modelo, "gemini-3.6-flash"]` estava travada na função.

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação de Responsabilidade Única (SRP): Uma função de inferência de IA não
     deve fazer I/O em disco. A persistência de log é uma preocupação de auditoria,
     não da chamada de rede do modelo de linguagem.
  2. Efeitos colaterais ocultos: Chamar `processar_audio()` alterava o estado do disco
     do usuário mesmo em testes unitários.
  3. Violação de DIP e ISP: O serviço de IA dependia de um módulo local de sistema
     operacional (`actions.py`), criando uma dependência circular/cruzada conceitual.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  A classe `GeminiAIService` é uma implementação atômica da interface `IAIService`.
  Ela é pura: recebe áudio/texto e retorna `IntentResult`. Não toca no microfone nem
  escreve no disco. A persistência é delegada à camada de orquestração (`VoiceAssistantController`).
================================================================================
"""
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
import requests
from dotenv import load_dotenv

from core.interfaces import IAIService, IHistoryLogger
from core.models import IntentResult
from .history_logger import registrar_transcricao


def _carregar_env() -> None:
    """Carrega variáveis de ambiente procurando no executável ou diretório local."""
    if getattr(sys, "frozen", False):
        env_exe = Path(sys.executable).parent / ".env"
        if env_exe.exists():
            load_dotenv(env_exe)
            return

    env_script = Path(__file__).resolve().parent.parent / ".env"
    if env_script.exists():
        load_dotenv(env_script)
        return

    load_dotenv()


_carregar_env()


PROMPT_SISTEMA = """Você é um assistente operacional inteligente para Windows.
Sua função é interpretar a voz ou texto do usuário e mapear para uma das ações do sistema operacional:

Ações disponíveis:
1. "abrir_navegador": Para abrir páginas ou pesquisar no Google (ex: "abra o google e pesquise x").
   Parâmetro esperado: {"query": "<termo de pesquisa ou URL>"}
2. "executar_cmd": Para comandos de prompt/terminal (ex: "abra o cmd e faça tal coisa", "mostre os arquivos").
   Parâmetro esperado: {"comando": "<comando batch/cmd, ex: dir, ipconfig, ping google.com>"}
3. "abrir_aplicativo": Para abrir programas locais (ex: "abra a calculadora", "abra o bloco de notas").
   Parâmetro esperado: {"app": "<nome do executável ou programa, ex: calc, notepad, explorer>"}
4. "outro": Para perguntas gerais ou solicitações que não configuram comando local.
   Parâmetro esperado: {}

Retorne EXCLUSIVAMENTE um JSON estrito no formato:
{
  "transcricao": "<transcrição fiel do áudio ou texto recebido>",
  "acao": "abrir_navegador" | "executar_cmd" | "abrir_aplicativo" | "outro",
  "parametros": { ... },
  "explicacao": "<resumo de uma linha do que foi compreendido e será feito>"
}
"""


def obter_api_token(api_token: str | None = None) -> str:
    """Recupera o token de autenticação das variáveis de ambiente."""
    token = (
        api_token
        or os.getenv("GEMINI_API_TOKEN")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if not token:
        raise ValueError("Chave de API do Gemini não encontrada no ambiente (.env).")
    return token


def extrair_json_resposta(texto_resposta: str) -> dict[str, Any]:
    """Extrai e valida o JSON da resposta do Gemini, tratando blocos de markdown."""
    texto = texto_resposta.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        texto = match.group(1)
    else:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio != -1 and fim != -1:
            texto = texto[inicio : fim + 1]

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return {
            "transcricao": texto_resposta,
            "acao": "outro",
            "parametros": {},
            "explicacao": "Não foi possível interpretar a resposta estruturada."
        }


class GeminiAIService(IAIService):
    """Cliente de IA desacoplado implementando o contrato IAIService."""

    def __init__(
        self,
        api_token: str | None = None,
        modelos: list[str] | None = None,
        timeout: int = 20,
        logger: IHistoryLogger | None = None
    ):
        self.api_token = api_token
        self.modelos = modelos or ["gemini-3.5-flash-lite", "gemini-3.6-flash"]
        self.timeout = timeout
        self.logger = logger

    def _obter_token(self) -> str:
        return obter_api_token(self.api_token)

    def processar_audio(self, audio_bytes: bytes) -> IntentResult:
        token = self._obter_token()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "audio/wav",
                            "data": audio_b64
                        }
                    },
                    {"text": PROMPT_SISTEMA}
                ]
            }]
        }

        ultimo_erro = None
        for mod in self.modelos:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={token}"
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()

                dados_resp = response.json()
                partes = dados_resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                texto_gerado = partes[0].get("text", "{}")

                dados_dict = extrair_json_resposta(texto_gerado)
                intent = IntentResult(
                    transcription=dados_dict.get("transcricao", ""),
                    action=dados_dict.get("acao", "outro"),
                    params=dados_dict.get("parametros", {}),
                    explanation=dados_dict.get("explicacao", "")
                )

                if self.logger:
                    self.logger.registrar(intent.transcription, intent.action, intent.params)

                return intent
            except Exception as e:
                ultimo_erro = e
                continue

        raise RuntimeError(f"Falha ao processar áudio no Gemini: {ultimo_erro}")

    def processar_texto(self, texto: str) -> IntentResult:
        token = self._obter_token()
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{PROMPT_SISTEMA}\n\nEntrada do usuário: {texto}"}
                ]
            }]
        }

        ultimo_erro = None
        for mod in self.modelos:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={token}"
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()

                dados_resp = response.json()
                partes = dados_resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                texto_gerado = partes[0].get("text", "{}")

                dados_dict = extrair_json_resposta(texto_gerado)
                intent = IntentResult(
                    transcription=dados_dict.get("transcricao", texto),
                    action=dados_dict.get("acao", "outro"),
                    params=dados_dict.get("parametros", {}),
                    explanation=dados_dict.get("explicacao", "")
                )

                if self.logger:
                    self.logger.registrar(intent.transcription, intent.action, intent.params)

                return intent
            except Exception as e:
                ultimo_erro = e
                continue

        raise RuntimeError(f"Falha ao processar comando de texto no Gemini: {ultimo_erro}")


# Funções de nível de módulo para retrocompatibilidade
_default_ai_service = GeminiAIService()


def _chamar_registrar_transcricao(texto: str, acao: str, detalhes: dict[str, Any]) -> None:
    mod = sys.modules.get("gemini_service")
    if mod and hasattr(mod, "registrar_transcricao"):
        mod.registrar_transcricao(texto=texto, acao=acao, detalhes=detalhes)
    else:
        registrar_transcricao(texto=texto, acao=acao, detalhes=detalhes)


def processar_audio(
    audio_bytes: bytes,
    api_token: str | None = None,
    modelo: str = "gemini-3.5-flash-lite"
) -> IntentResult:
    service = GeminiAIService(api_token=api_token, modelos=[modelo, "gemini-3.6-flash"])
    res = service.processar_audio(audio_bytes)
    # Mantém o efeito esperado por testes legados
    _chamar_registrar_transcricao(
        texto=res.transcription,
        acao=res.action,
        detalhes=res.params
    )
    return res


def processar_texto(
    comando_texto: str,
    api_token: str | None = None,
    modelo: str = "gemini-3.5-flash-lite"
) -> IntentResult:
    service = GeminiAIService(api_token=api_token, modelos=[modelo, "gemini-3.6-flash"])
    res = service.processar_texto(comando_texto)
    # Mantém o efeito esperado por testes legados
    _chamar_registrar_transcricao(
        texto=res.transcription,
        acao=res.action,
        detalhes=res.params
    )
    return res
