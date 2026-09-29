"""Testes dedicados à validação dos princípios SOLID implementados no projeto."""
import pytest
from core.models import IntentResult, ActionResult
from core.interfaces import IAudioRecorder, IAIService, IActionHandler, IHistoryLogger
from actions.dispatcher import ActionDispatcher
from actions.base import BaseActionHandler
from services.controller import VoiceAssistantController


# 1. TESTE DO PRINCÍPIO ABERTO/FECHADO (OCP)
class CustomVolumeHandler(BaseActionHandler):
    """Nova ação criada para estender o sistema sem modificar código existente."""

    @property
    def nome_acao(self) -> str:
        return "ajustar_volume"

    def executar(self, parametros: dict, contexto: IntentResult | None = None) -> ActionResult:
        nivel = parametros.get("nivel", 50)
        return ActionResult(
            status=f"Volume ajustado para {nivel}%",
            saida=f"Windows CoreAudio: volume={nivel}",
            acao=self.nome_acao,
            success=True
        )


def test_ocp_adicionar_novo_handler_sem_modificar_dispatcher():
    dispatcher = ActionDispatcher()
    # Registra a nova funcionalidade dinamicamente (Aberto para extensão)
    dispatcher.registrar_handler(CustomVolumeHandler())

    intent = IntentResult(
        transcription="ajuste o volume para 80 porcento",
        action="ajustar_volume",
        params={"nivel": 80},
        explanation="Ajustar o volume do áudio"
    )

    resultado = dispatcher.despachar(intent)
    assert resultado.success is True
    assert resultado.acao == "ajustar_volume"
    assert "80%" in resultado.status


# 2. TESTE DA SUBSTITUIÇÃO DE LISKOV (LSP)
def test_lsp_action_result_contrato_consistente():
    res = ActionResult(
        status="Sucesso",
        saida="Linha de comando executada",
        acao="executar_cmd",
        comando="dir",
        success=True
    )
    # Acesso via atributo (estilo objeto)
    assert res.status == "Sucesso"
    assert res.output == "Linha de comando executada"
    assert res.saida == "Linha de comando executada"

    # Acesso via chave (estilo dicionário)
    assert res["status"] == "Sucesso"
    assert res["saida"] == "Linha de comando executada"
    assert res.get("acao") == "executar_cmd"
    assert res.get("inexistente", "padrao") == "padrao"


# 3. TESTE DA INVERSÃO DE DEPENDÊNCIA (DIP) COM MOCKS/STUBS
class FakeRecorder(IAudioRecorder):
    def __init__(self):
        self._gravando = False

    def iniciar(self) -> None:
        self._gravando = True

    def parar(self) -> bytes:
        self._gravando = False
        return b"fake_wav_bytes"

    def cancelar(self) -> None:
        self._gravando = False

    def esta_gravando(self) -> bool:
        return self._gravando


class FakeAIService(IAIService):
    def processar_audio(self, audio_bytes: bytes) -> IntentResult:
        return IntentResult(
            transcription="abra a calculadora",
            action="abrir_aplicativo",
            params={"app": "calc"},
            explanation="Abrir calculadora"
        )

    def processar_texto(self, texto: str) -> IntentResult:
        return IntentResult(
            transcription=texto,
            action="abrir_navegador",
            params={"query": "python"},
            explanation="Pesquisar python"
        )


class FakeLogger(IHistoryLogger):
    def __init__(self):
        self.logs = []

    def registrar(self, texto: str, acao: str, detalhes: dict) -> None:
        self.logs.append({"texto": texto, "acao": acao, "detalhes": detalhes})


def test_dip_controller_com_implementacoes_abstratas():
    fake_rec = FakeRecorder()
    fake_ai = FakeAIService()
    fake_logger = FakeLogger()
    dispatcher = ActionDispatcher()

    # O controlador é instanciado recebendo abstrações, sem acoplamento a rede ou hardware
    controller = VoiceAssistantController(
        recorder=fake_rec,
        ai_service=fake_ai,
        dispatcher=dispatcher,
        logger=fake_logger
    )

    controller.iniciar_gravacao()
    assert fake_rec.esta_gravando() is True

    intent, action_res = controller.finalizar_e_processar_voz()
    assert fake_rec.esta_gravando() is False
    assert intent.transcription == "abra a calculadora"
    assert action_res.action == "abrir_aplicativo"

    # Verifica se o logger registrou a ação
    assert len(fake_logger.logs) == 1
    assert fake_logger.logs[0]["acao"] == "abrir_aplicativo"
