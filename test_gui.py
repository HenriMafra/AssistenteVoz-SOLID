from unittest.mock import patch, MagicMock
import pytest
from app_gui import AssistenteVozGUI

def test_assistente_voz_gui_init_e_cancelar():
    with patch("tkinter.Tk") as mock_tk, \
         patch("app_gui.AssistenteVozGUI._verificar_conexao"):
        mock_root = MagicMock()
        
        with patch("tkinter.Frame"), patch("tkinter.Label"), patch("tkinter.Button"), patch("tkinter.Entry"):
            gui = AssistenteVozGUI(mock_root)
            assert gui.esta_gravando is False
            assert gui.processando is False

            # Testa cancelamento
            gui.esta_gravando = True
            gui.processando = True
            with patch.object(gui.gravador, "cancelar") as mock_cancel:
                gui._cancelar_operacao()
                assert gui.cancelado is True
                assert gui.esta_gravando is False
                assert gui.processando is False
                mock_cancel.assert_called_once()

def test_assistente_voz_gui_atualizar_sucesso():
    with patch("tkinter.Tk") as mock_tk, \
         patch("app_gui.AssistenteVozGUI._verificar_conexao"):
        mock_root = MagicMock()
        with patch("tkinter.Frame"), patch("tkinter.Label"), patch("tkinter.Button"), patch("tkinter.Entry"):
            gui = AssistenteVozGUI(mock_root)
            resultado = {
                "transcricao": "abra o google",
                "acao": "abrir_navegador",
                "parametros": {"query": "python"},
                "explicacao": "Abrir o Google e buscar python"
            }
            gui._atualizar_sucesso(resultado, "Navegador aberto com sucesso")
            gui.txt_compreendido.config.assert_called()
            gui.txt_vai_executar.config.assert_called()
