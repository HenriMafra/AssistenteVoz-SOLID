"""Controlador da Aplicação (Caso de Uso) aplicando Dependency Inversion Principle (DIP).

================================================================================
DIAGNÓSTICO ARQUITETURAL SOLID:
- O QUE O CÓDIGO LEGADO FAZIA:
  Não existia camada de aplicação/controlador. A interface gráfica (app_gui.py)
  e o terminal (main.py) duplicavam manualmente todo o pipeline:
  capturar som -> chamar processar_audio() -> chamar executar_acao_estruturada() -> salvar log.

- POR QUE ESSA PRÁTICA ERA CRÍTICA (FALHA DE DESIGN):
  1. Violação de Inversão de Dependência (DIP): As interfaces de usuário dependiam
     diretamente dos detalhes técnicos de baixo nível.
  2. Duplicação de Regras de Negócio (DRY): Qualquer alteração na lógica (ex: adicionar
     uma confirmação do usuário ou trocar o provedor de IA) precisava ser replicada
     em múltiplos arquivos.

- O QUE ESTE CÓDIGO FAZ AGORA E COMO ARRUMA:
  Cria a classe `VoiceAssistantController`, que atua como orquestrador central de
  casos de uso. Ela recebe exclusivamente abstrações no seu construtor
  (`IAudioRecorder`, `IAIService`, `IHistoryLogger`), permitindo plugar mocks em testes
  ou trocar serviços inteiros em tempo de execução sem alterar a interface de usuário.
================================================================================
"""
from typing import Any
from core.interfaces import IAudioRecorder, IAIService, IHistoryLogger
from core.models import ActionResult, IntentResult
from actions.dispatcher import ActionDispatcher
from .audio_recorder import SoundDeviceRecorder
from .gemini_service import GeminiAIService, obter_api_token
from .history_logger import MarkdownHistoryLogger


class VoiceAssistantController:
    """Orquestrador central de casos de uso do assistente de voz (DIP)."""

    def __init__(
        self,
        recorder: IAudioRecorder | None = None,
        ai_service: IAIService | None = None,
        dispatcher: ActionDispatcher | None = None,
        logger: IHistoryLogger | None = None
    ):
        self.recorder = recorder or SoundDeviceRecorder()
        self.ai_service = ai_service or GeminiAIService()
        self.dispatcher = dispatcher or ActionDispatcher()
        self.logger = logger or MarkdownHistoryLogger()

    def verificar_conexao(self) -> bool:
        """Verifica se o token de acesso da IA está configurado."""
        try:
            obter_api_token()
            return True
        except Exception:
            return False

    def iniciar_gravacao(self) -> None:
        """Inicia captura de áudio via interface de gravação."""
        self.recorder.iniciar()

    def cancelar_gravacao(self) -> None:
        """Aborta e descarta a gravação corrente."""
        self.recorder.cancelar()

    def esta_gravando(self) -> bool:
        """Verifica se o gravador está em operação."""
        return self.recorder.esta_gravando()

    def finalizar_e_processar_voz(self) -> tuple[IntentResult, ActionResult]:
        """Finaliza a captura de áudio, envia para a IA, despacha a ação e registra no log."""
        audio_bytes = self.recorder.parar()
        return self.processar_audio_bytes(audio_bytes)

    def processar_audio_bytes(self, audio_bytes: bytes) -> tuple[IntentResult, ActionResult]:
        """Processa bytes de áudio diretamente."""
        intent = self.ai_service.processar_audio(audio_bytes)
        result = self.dispatcher.despachar(intent)
        self.logger.registrar(intent.transcription, intent.action, intent.params)
        return intent, result

    def processar_comando_texto(self, texto: str) -> tuple[IntentResult, ActionResult]:
        """Interpreta texto digitado pelo usuário, despacha ação e registra no log."""
        intent = self.ai_service.processar_texto(texto)
        result = self.dispatcher.despachar(intent)
        self.logger.registrar(intent.transcription, intent.action, intent.params)
        return intent, result
