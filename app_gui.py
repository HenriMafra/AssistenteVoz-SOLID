"""Ponto de entrada para a Interface Gráfica do Assistente de Voz."""
from ui.app_gui import AssistenteVozGUI, iniciar_gui

__all__ = ["AssistenteVozGUI", "iniciar_gui"]

if __name__ == "__main__":
    iniciar_gui()
