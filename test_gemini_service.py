import json
import pytest
from unittest.mock import patch, MagicMock

from gemini_service import (
    extrair_json_resposta,
    processar_texto,
    processar_audio,
)

def test_extrair_json_resposta_puro():
    raw = '{"transcricao": "olá mundo", "acao": "outro", "parametros": {}, "explicacao": "teste"}'
    res = extrair_json_resposta(raw)
    assert res["transcricao"] == "olá mundo"
    assert res["acao"] == "outro"

def test_extrair_json_resposta_markdown():
    raw = '```json\n{"transcricao": "abra o google", "acao": "abrir_navegador", "parametros": {"query": "python"}, "explicacao": "busca"}\n```'
    res = extrair_json_resposta(raw)
    assert res["acao"] == "abrir_navegador"
    assert res["parametros"]["query"] == "python"

def test_processar_texto_mock():
    mock_gemini_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "transcricao": "abra o cmd e digite dir",
                        "acao": "executar_cmd",
                        "parametros": {"comando": "dir"},
                        "explicacao": "Executar dir no CMD"
                    })
                }]
            }
        }]
    }

    with patch("requests.post") as mock_post, patch("gemini_service.registrar_transcricao") as mock_reg:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: mock_gemini_response)
        
        resultado = processar_texto("abra o cmd e digite dir", api_token="fake_token")
        
        assert resultado["transcricao"] == "abra o cmd e digite dir"
        assert resultado["acao"] == "executar_cmd"
        assert resultado["parametros"]["comando"] == "dir"
        mock_reg.assert_called_once()


def test_processar_audio_mock():
    mock_gemini_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "transcricao": "pesquise notícias de inteligência artificial",
                        "acao": "abrir_navegador",
                        "parametros": {"query": "notícias de inteligência artificial"},
                        "explicacao": "Abrir Google e pesquisar"
                    })
                }]
            }
        }]
    }

    with patch("requests.post") as mock_post, patch("gemini_service.registrar_transcricao") as mock_reg:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: mock_gemini_response)
        
        resultado = processar_audio(b"fake_wav_bytes", api_token="fake_token")
        
        assert resultado["transcricao"] == "pesquise notícias de inteligência artificial"
        assert resultado["acao"] == "abrir_navegador"
        mock_reg.assert_called_once()


def test_gravador_audio():
    from gemini_service import GravadorAudio
    import numpy as np

    gravador = GravadorAudio(samplerate=16000)
    assert not gravador.esta_gravando()

    with patch("sounddevice.InputStream") as mock_stream:
        gravador.iniciar()
        assert gravador.esta_gravando()
        # Simula recepção de frames
        dummy_frame = np.zeros((1600, 1), dtype=np.int16)
        gravador._audio_frames.append(dummy_frame)
        
        wav_bytes = gravador.parar()
        assert not gravador.esta_gravando()
        assert isinstance(wav_bytes, bytes)
        assert len(wav_bytes) > 44  # cabeçalho WAV tem 44 bytes

    with patch("sounddevice.InputStream") as mock_stream:
        gravador.iniciar()
        assert gravador.esta_gravando()
        gravador.cancelar()
        assert not gravador.esta_gravando()
        assert len(gravador._audio_frames) == 0



