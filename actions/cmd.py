"""Handler responsável exclusivamente pela execução de comandos no Windows Prompt (CMD)."""
import subprocess
from typing import Any
from core.models import ActionResult, IntentResult
from .base import BaseActionHandler


def executar_cmd(comando: str, interativo: bool = True) -> subprocess.CompletedProcess | subprocess.Popen:
    """Executa comando no CMD.
    
    Se interativo=True, abre janela visível do CMD.
    Se interativo=False, executa síncrono capturando stdout/stderr.
    """
    if interativo:
        return subprocess.Popen(f"cmd.exe /k {comando}", shell=True)
    return subprocess.run(
        comando,
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
        encoding="cp850",
        errors="replace"
    )


class CmdActionHandler(BaseActionHandler):
    """Executa comandos locais no Prompt de Comando (CMD) do Windows (SRP)."""

    @property
    def nome_acao(self) -> str:
        return "executar_cmd"

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        comando = parametros.get("comando", "dir")
        transcricao = (contexto.transcription.lower() if contexto else "")

        # 1. Executa em background para capturar o retorno real do comando
        try:
            res_bg = executar_cmd(comando, interativo=False)
            saida_stdout = getattr(res_bg, "stdout", "") or ""
            saida_stderr = getattr(res_bg, "stderr", "") or ""

            if saida_stdout.strip():
                saida_cmd = saida_stdout.strip()
            elif saida_stderr.strip():
                saida_cmd = f"[Aviso/Erro]:\n{saida_stderr.strip()}"
            else:
                saida_cmd = "Comando executado com sucesso (sem retorno de texto)."
        except Exception as e:
            saida_cmd = f"Erro na execução: {e}"

        # 2. Se a intenção solicitou explicitamente abrir janela do terminal
        termos_janela = ("cmd", "prompt", "terminal", "abrir")
        if any(termo in transcricao for termo in termos_janela):
            try:
                executar_cmd(comando, interativo=True)
            except Exception:
                pass

        return ActionResult(
            status=f"CMD executado com: '{comando}'",
            saida=saida_cmd,
            acao=self.nome_acao,
            comando=comando,
            success=True
        )
