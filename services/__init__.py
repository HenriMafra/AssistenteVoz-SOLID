"""Módulo de Serviços do Assistente de Voz."""
from .audio_recorder import (
    SoundDeviceRecorder,
    GravadorAudio,
    gravar_audio_interativo,
    gravar_audio_segundos,
)
from .gemini_service import (
    GeminiAIService,
    processar_audio,
    processar_texto,
    obter_api_token,
    extrair_json_resposta,
    PROMPT_SISTEMA,
)
from .history_logger import MarkdownHistoryLogger, registrar_transcricao
from .controller import VoiceAssistantController

__all__ = [
    "SoundDeviceRecorder",
    "GravadorAudio",
    "gravar_audio_interativo",
    "gravar_audio_segundos",
    "GeminiAIService",
    "processar_audio",
    "processar_texto",
    "obter_api_token",
    "extrair_json_resposta",
    "PROMPT_SISTEMA",
    "MarkdownHistoryLogger",
    "registrar_transcricao",
    "VoiceAssistantController",
]
