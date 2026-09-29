"""Serviço responsável exclusivamente pela captura e bufferização de áudio do microfone (SRP)."""
import io
from typing import Any
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from core.interfaces import IAudioRecorder


class SoundDeviceRecorder(IAudioRecorder):
    """Implementação concreta de captura de áudio com sounddevice e scipy."""

    def __init__(self, samplerate: int = 16000):
        self.samplerate = samplerate
        self._audio_frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._gravando: bool = False

    def _callback(self, indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        if self._gravando:
            self._audio_frames.append(indata.copy())

    def iniciar(self) -> None:
        """Inicia a gravação de áudio do microfone padrão."""
        self._audio_frames = []
        self._gravando = True
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="int16",
            callback=self._callback
        )
        self._stream.start()

    def parar(self) -> bytes:
        """Finaliza a gravação e retorna os bytes codificados em WAV (16kHz, mono)."""
        self._gravando = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if not self._audio_frames:
            raise ValueError("Nenhum áudio foi capturado.")

        audio_data = np.concatenate(self._audio_frames, axis=0)
        buffer = io.BytesIO()
        wavfile.write(buffer, self.samplerate, audio_data)
        return buffer.getvalue()

    def cancelar(self) -> None:
        """Cancela a gravação e descarta o buffer de áudio imediatamente."""
        self._gravando = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._audio_frames = []

    def esta_gravando(self) -> bool:
        return self._gravando


# Alias para retrocompatibilidade
GravadorAudio = SoundDeviceRecorder


def gravar_audio_interativo(samplerate: int = 16000) -> bytes:
    """Grava áudio do microfone padrão até que o usuário pressione ENTER no console."""
    gravador = SoundDeviceRecorder(samplerate=samplerate)
    print("\n[GRAVANDO] Fale agora o seu comando...")
    print("Pressione [ENTER] quando terminar de falar...")
    gravador.iniciar()
    input()
    return gravador.parar()


def gravar_audio_segundos(segundos: int = 5, samplerate: int = 16000) -> bytes:
    """Grava áudio do microfone por uma duração fixa em segundos."""
    print(f"\n[GRAVANDO] Fale durante {segundos} segundos...")
    gravacao = sd.rec(int(segundos * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    buffer = io.BytesIO()
    wavfile.write(buffer, samplerate, gravacao)
    return buffer.getvalue()
