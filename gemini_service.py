"""Módulo de fachada (Façade) retrocompatível para gemini_service.py.

Delega chamadas para a nova arquitetura orientada a SOLID (services/ e core/).
Garante total compatibilidade com códigos, testes e ferramentas existentes.
"""
from services.audio_recorder import (
    GravadorAudio,
    SoundDeviceRecorder,
    gravar_audio_interativo,
    gravar_audio_segundos,
)
from services.gemini_service import (
    GeminiAIService,
    PROMPT_SISTEMA,
    extrair_json_resposta,
    obter_api_token,
    processar_audio,
    processar_texto,
)
from services.history_logger import registrar_transcricao

__all__ = [
    "PROMPT_SISTEMA",
    "obter_api_token",
    "extrair_json_resposta",
    "GravadorAudio",
    "SoundDeviceRecorder",
    "gravar_audio_interativo",
    "gravar_audio_segundos",
    "processar_audio",
    "processar_texto",
    "registrar_transcricao",
    "GeminiAIService",
]
