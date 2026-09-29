from unittest.mock import patch, MagicMock
import pytest
from main import main

def test_main_arg_texto():
    with patch("sys.argv", ["main.py", "--texto", "abra o bloco de notas"]), \
         patch("main.processar_texto") as mock_proc, \
         patch("main.executar_acao_estruturada") as mock_exec:
        
        mock_proc.return_value = {
            "transcricao": "abra o bloco de notas",
            "acao": "abrir_aplicativo",
            "parametros": {"app": "notepad"},
            "explicacao": "Abrir bloco de notas"
        }
        mock_exec.return_value = "Aplicativo iniciado: 'notepad'"

        main()
        mock_proc.assert_called_once_with("abra o bloco de notas")
        mock_exec.assert_called_once()
