import os
import pytest
from unittest.mock import patch, MagicMock

# Importação dos módulos que serão implementados
from actions import (
    abrir_navegador,
    executar_cmd,
    abrir_aplicativo,
    registrar_transcricao,
    executar_acao_estruturada
)

def test_abrir_navegador_url():
    with patch("webbrowser.open") as mock_open:
        abrir_navegador("https://www.google.com")
        mock_open.assert_called_once_with("https://www.google.com")

def test_abrir_navegador_busca():
    with patch("webbrowser.open") as mock_open:
        abrir_navegador("previsão do tempo")
        mock_open.assert_called_once_with("https://www.google.com/search?q=previs%C3%A3o+do+tempo")

def test_executar_cmd_interativo():
    with patch("subprocess.Popen") as mock_popen:
        executar_cmd("dir", interativo=True)
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert "cmd.exe /k dir" in args[0]

def test_executar_cmd_background():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="ok", stderr="", returncode=0)
        res = executar_cmd("echo hello", interativo=False)
        assert res.returncode == 0
        mock_run.assert_called_once()

def test_abrir_aplicativo_conhecido():
    with patch("subprocess.Popen") as mock_popen:
        abrir_aplicativo("calculadora")
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert "calc" in args[0]

def test_registrar_transcricao(tmp_path):
    arquivo_md = tmp_path / "transcricao_teste.md"
    registrar_transcricao(
        texto="abra o google e pesquise sobre inteligência artificial",
        acao="abrir_navegador",
        detalhes={"query": "inteligência artificial"},
        arquivo=str(arquivo_md)
    )
    assert arquivo_md.exists()
    conteudo = arquivo_md.read_text(encoding="utf-8")
    assert "abra o google e pesquise sobre inteligência artificial" in conteudo
    assert "abrir_navegador" in conteudo

def test_executar_acao_estruturada():
    dados = {
        "acao": "abrir_navegador",
        "parametros": {"query": "noticias de tecnologia"},
        "explicacao": "Abrindo o Google para pesquisar notícias"
    }
    with patch("actions.abrir_navegador") as mock_nav:
        executar_acao_estruturada(dados)
        mock_nav.assert_called_once_with("noticias de tecnologia")
