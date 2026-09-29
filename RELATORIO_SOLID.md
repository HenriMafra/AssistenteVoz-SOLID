# Relatório Completo de Transformação SOLID: O Que Fazia, Como Fazia, O Que Faz Agora e Como Faz Agora

Este documento detalha exaustivamente cada módulo do projeto **Assistente de Voz para Windows**, demonstrando a evolução entre a versão legada (`AssistenteVoz`) e a versão arquitetada em SOLID (`AssistenteVoz_SOLID`), fundamentando cada decisão nos 5 princípios do [FreeCodeCamp](https://www.freecodecamp.org/portuguese/news/os-principios-solid-da-programacao-orientada-a-objetos-explicados-em-bom-portugues/).

---

## 1. Módulo de Apresentação e Interface Gráfica

### 1.1. Arquivo Legado: `AssistenteVoz/app_gui.py`

#### O que o código fazia:
A classe `AssistenteVozGUI` era uma **God Class** de 738 linhas. Ela não apenas desenhava a janela na tela, mas também assumia o papel de operadora de hardware de som, cliente de rede para a API de IA do Google Gemini na nuvem, executora de comandos do Prompt do Windows e gerenciadora de arquivos do sistema.

#### Como fazia (Código Legado):
```python
# AssistenteVoz/app_gui.py (Linhas 9-10)
# A interface gráfica importando diretamente detalhes de baixo nível e rede:
from actions import executar_acao_estruturada, abrir_aplicativo
from gemini_service import GravadorAudio, processar_audio, processar_texto, obter_api_token

class AssistenteVozGUI:
    def __init__(self, root: tk.Tk):
        # Linha 48: Instanciação rígida do microfone dentro da GUI
        self.gravador = GravadorAudio(samplerate=16000)
        ...

    # Linhas 548-562: Thread visual executando IA e comandos de SO
    def _worker_processar_audio(self):
        try:
            wav_bytes = self.gravador.parar()
            if self.cancelado:
                return

            # A UI chamando a API do Gemini via HTTP:
            resultado = processar_audio(wav_bytes)
            if self.cancelado:
                return

            # A UI disparando processos no Windows (CMD, Navegador, etc.):
            status = executar_acao_estruturada(resultado)
            if self.cancelado:
                return

            self.root.after(0, self._atualizar_sucesso, resultado, status)
        except Exception as e:
            ...

    # Linhas 624-636: Processamento de texto direto da UI
    def _worker_processar_texto(self, comando: str):
        try:
            resultado = processar_texto(comando)
            status = executar_acao_estruturada(resultado)
            self.root.after(0, self._atualizar_sucesso, resultado, status)
        except Exception as e:
            ...
```

---

### 1.2. Novo Arquivo: `AssistenteVoz_SOLID/ui/app_gui.py`

#### O que faz agora:
A classe `AssistenteVozGUI` foi convertida em uma **View estrita e desacoplada**. Sua única e exclusiva responsabilidade é a apresentação visual (desenhar botões, caixas de texto e ondas sonoras). Ela não conhece mais a API do Gemini, não sabe como o microfone grava e não sabe como o Windows executa processos. Toda a inteligência e orquestração foram delegadas ao `VoiceAssistantController`.

#### Como faz agora (Código Refatorado):
```python
# AssistenteVoz_SOLID/ui/app_gui.py (Linhas 15-28)
# A GUI importa apenas modelos de domínio e o controlador de aplicação:
from core.models import ActionResult, IntentResult
from services.controller import VoiceAssistantController

class AssistenteVozGUI:
    def __init__(self, root: tk.Tk, controller: VoiceAssistantController | None = None):
        self.root = root
        # Injeção de dependência (DIP): O controlador pode ser mockado em testes
        self.controller = controller or VoiceAssistantController()
        ...

    # Linhas 545-555: Worker desacoplado
    def _worker_processar_audio(self):
        try:
            # A GUI apenas avisa o Controller: "Processe a voz do usuário"
            intent, status = self.controller.finalizar_e_processar_voz()
            if self.cancelado:
                return
            self.root.after(0, self._atualizar_sucesso, intent, status)
        except Exception as e:
            if not self.cancelado:
                self.root.after(0, self._atualizar_erro, str(e))

    # Linhas 585-595: Worker de texto desacoplado
    def _worker_processar_texto(self, comando: str):
        try:
            # A GUI apenas avisa o Controller: "Processe este texto"
            intent, status = self.controller.processar_comando_texto(comando)
            if self.cancelado:
                return
            self.root.after(0, self._atualizar_sucesso, intent, status)
        except Exception as e:
            if not self.cancelado:
                self.root.after(0, self._atualizar_erro, str(e))
```

---

## 2. Módulo de IA, Áudio e Persistência

### 2.1. Arquivo Legado: `AssistenteVoz/gemini_service.py`

#### O que o código fazia:
Acumulava **7 responsabilidades distintas** em um único arquivo: gerenciava variáveis de ambiente, validação de tokens, montagem de prompts, captura de microfone via `sounddevice`, manipulação de matrizes com NumPy/SciPy, requisições HTTP REST com `requests` e gravação de arquivos Markdown no disco.

#### Como fazia (Código Legado):
```python
# AssistenteVoz/gemini_service.py

# Linha 13: Dependência inadequada do módulo de ações locais
from actions import registrar_transcricao

# Linhas 88-128: Hardware de áudio misturado no cliente de IA
class GravadorAudio:
    def __init__(self, samplerate: int = 16000):
        self.samplerate = samplerate
        self._audio_frames = []
        self._stream = None
        self._gravando = False

    def iniciar(self) -> None:
        self._stream = sd.InputStream(samplerate=self.samplerate, channels=1, dtype="int16", callback=self._callback)
        self._stream.start()

    def parar(self) -> bytes:
        ...
        audio_data = np.concatenate(self._audio_frames, axis=0)
        buffer = io.BytesIO()
        wavfile.write(buffer, self.samplerate, audio_data)
        return buffer.getvalue()

# Linhas 167-205: Inferência com efeito colateral de gravação em disco
def processar_audio(audio_bytes: bytes, api_token: str | None = None, modelo: str = "gemini-3.5-flash-lite") -> dict:
    ...
    response = requests.post(url, json=payload, timeout=20)
    ...
    resultado = extrair_json_resposta(texto_gerado)
    
    # EFEITO COLATERAL OCULTO: Toda inferência gravava em disco compulsoriamente
    registrar_transcricao(
        texto=resultado.get("transcricao", ""),
        acao=resultado.get("acao", "outro"),
        detalhes=resultado.get("parametros", {})
    )
    return resultado
```

---

### 2.2. Novos Arquivos Refatorados (SRP e DIP)

O monólito foi quebrado em **3 serviços atômicos e especializados**:

#### A. Captura de Áudio: `AssistenteVoz_SOLID/services/audio_recorder.py`
**O que faz agora**: Cuida exclusivamente de interagir com o microfone e converter para WAV. Não conhece IA nem arquivos de log.
```python
# AssistenteVoz_SOLID/services/audio_recorder.py (Linhas 11-53)
class SoundDeviceRecorder(IAudioRecorder):
    def __init__(self, samplerate: int = 16000):
        self.samplerate = samplerate
        self._audio_frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._gravando: bool = False

    def iniciar(self) -> None:
        self._audio_frames = []
        self._gravando = True
        self._stream = sd.InputStream(samplerate=self.samplerate, channels=1, dtype="int16", callback=self._callback)
        self._stream.start()

    def parar(self) -> bytes:
        self._gravando = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
        audio_data = np.concatenate(self._audio_frames, axis=0)
        buffer = io.BytesIO()
        wavfile.write(buffer, self.samplerate, audio_data)
        return buffer.getvalue()
```

#### B. Cliente de IA Puro: `AssistenteVoz_SOLID/services/gemini_service.py`
**O que faz agora**: Cuida exclusivamente da comunicação HTTP REST com a API do Gemini. É uma função pura de inferência: recebe áudio/texto e retorna `IntentResult`. Não toca no microfone nem escreve em disco.
```python
# AssistenteVoz_SOLID/services/gemini_service.py (Linhas 97-150)
class GeminiAIService(IAIService):
    def __init__(self, api_token: str | None = None, modelos: list[str] | None = None):
        self.api_token = api_token
        self.modelos = modelos or ["gemini-3.5-flash-lite", "gemini-3.6-flash"]

    def processar_audio(self, audio_bytes: bytes) -> IntentResult:
        token = self._obter_token()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}, {"text": PROMPT_SISTEMA}]}]}
        
        response = requests.post(url, json=payload, timeout=20)
        dados_dict = extrair_json_resposta(texto_gerado)
        
        # Retorna DTO tipado e puro (sem efeitos colaterais de I/O em disco):
        return IntentResult(
            transcription=dados_dict.get("transcricao", ""),
            action=dados_dict.get("acao", "outro"),
            params=dados_dict.get("parametros", {}),
            explanation=dados_dict.get("explicacao", "")
        )
```

#### C. Persistência Isolada: `AssistenteVoz_SOLID/services/history_logger.py`
**O que faz agora**: Cuida exclusivamente de formatar e anexar o histórico no arquivo `transcricao.md`.
```python
# AssistenteVoz_SOLID/services/history_logger.py (Linhas 32-52)
class MarkdownHistoryLogger(IHistoryLogger):
    def __init__(self, arquivo_destino: str = "transcricao.md"):
        self.arquivo_destino = arquivo_destino

    def registrar(self, texto: str, acao: str, detalhes: dict[str, Any]) -> None:
        registrar_transcricao(texto=texto, acao=acao, detalhes=detalhes, arquivo=self.arquivo_destino)
```

---

## 3. Módulo de Execução de Ações Locais

### 3.1. Arquivo Legado: `AssistenteVoz/actions.py`

#### O que o código fazia:
- Utilizava um bloco `if-elif-else` monolítico e engessado para decidir qual ação rodar.
- A classe `ResultadoAcao` fingia ser um dicionário mas não implementava o contrato completo (LSP).
- Fazia parsing léxico de strings no meio do executor do CMD (`if "cmd" in transcricao...`).
- Misturava gravação de arquivo Markdown com código de sistema operacional.

#### Como fazia (Código Legado):
```python
# AssistenteVoz/actions.py

# Linhas 25-41: Falso dicionário violando LSP
class ResultadoAcao:
    def __init__(self, status: str, saida: str = "", acao: str = "", comando: str = ""):
        self.status = status
        self.saida = saida
        self.acao = acao
        self.comando = comando
    def get(self, chave: str, padrao=None):
        return getattr(self, chave, padrao)
    def __getitem__(self, chave: str):
        return getattr(self, chave)

# Linhas 95-150: Violação grave de OCP (fechado para extensão)
def executar_acao_estruturada(dados: dict) -> ResultadoAcao:
    acao = dados.get("acao", "outro")
    params = dados.get("parametros", {})
    transcricao = dados.get("transcricao", "").lower()

    if acao == "abrir_navegador":
        query = params.get("query") or params.get("url") or ""
        abrir_navegador(query)
        ...
    elif acao == "executar_cmd":
        comando = params.get("comando", "dir")
        res_bg = executar_cmd(comando, interativo=False)
        # Violação de SRP: Análise de texto no executor de sistema
        if "cmd" in transcricao or "prompt" in transcricao:
            executar_cmd(comando, interativo=True)
        ...
    elif acao == "abrir_aplicativo":
        app = params.get("app", "")
        abrir_aplicativo(app)
        ...
```

---

### 3.2. Novos Arquivos Refatorados (Command / Strategy e OCP)

O despachante agora é **aberto para extensão e fechado para modificação**. Novas ações são adicionadas criando uma classe isolada sem nunca alterar o código existente.

#### A. Manipulador de Navegador: `AssistenteVoz_SOLID/actions/browser.py`
```python
# AssistenteVoz_SOLID/actions/browser.py (Linhas 23-48)
class BrowserActionHandler(BaseActionHandler):
    @property
    def nome_acao(self) -> str:
        return "abrir_navegador"

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        query = (parametros.get("query") or parametros.get("url") or "").strip()
        url_final = abrir_navegador(query)
        return ActionResult(status=f"Navegador aberto com: '{query}'", saida=f"Pesquisa: {url_final}", acao=self.nome_acao)
```

#### B. Manipulador de Terminal: `AssistenteVoz_SOLID/actions/cmd.py`
```python
# AssistenteVoz_SOLID/actions/cmd.py (Linhas 32-65)
class CmdActionHandler(BaseActionHandler):
    @property
    def nome_acao(self) -> str:
        return "executar_cmd"

    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult:
        comando = parametros.get("comando", "dir")
        res_bg = executar_cmd(comando, interativo=False)
        saida_cmd = res_bg.stdout.strip() if hasattr(res_bg, "stdout") else "Sucesso."
        return ActionResult(status=f"CMD executado com: '{comando}'", saida=saida_cmd, acao=self.nome_acao, comando=comando)
```

#### C. Despachante Aberto para Extensão: `AssistenteVoz_SOLID/actions/dispatcher.py`
```python
# AssistenteVoz_SOLID/actions/dispatcher.py (Linhas 16-55)
class ActionDispatcher:
    def __init__(self, handlers: list[IActionHandler] | None = None):
        self._handlers: dict[str, IActionHandler] = {}
        # Registra os handlers padrão
        self.registrar_handler(BrowserActionHandler())
        self.registrar_handler(CmdActionHandler())
        self.registrar_handler(AppLauncherHandler())

    def registrar_handler(self, handler: IActionHandler) -> "ActionDispatcher":
        """Permite plugar novas ações sem alterar o despachante (OCP)."""
        self._handlers[handler.nome_acao] = handler
        return self

    def despachar(self, intent: IntentResult | dict[str, Any]) -> ActionResult:
        intent_obj = intent if isinstance(intent, IntentResult) else IntentResult(**intent)
        handler = self._handlers.get(intent_obj.action)
        if not handler:
            return ActionResult(status="Ação não suportada", saida="", acao="outro")
        return handler.executar(intent_obj.params, contexto=intent_obj)
```

---

## 4. Orquestrador de Aplicação (Caso de Uso)

### 4.1. Como Era Feito no Código Legado:
Tanto `app_gui.py` quanto `main.py` duplicavam o fluxo procedural:
1. Chamar `gravar()`
2. Chamar `processar_audio()`
3. Chamar `executar_acao_estruturada()`
4. Chamar `registrar_transcricao()`
Se uma etapa do fluxo mudasse, era preciso alterar dois lugares diferentes.

### 4.2. Como É Feito Agora: `AssistenteVoz_SOLID/services/controller.py`
Centralizado em uma classe orquestradora que depende unicamente de contratos abstratos (DIP):

```python
# AssistenteVoz_SOLID/services/controller.py (Linhas 18-55)
class VoiceAssistantController:
    def __init__(
        self,
        recorder: IAudioRecorder | None = None,
        ai_service: IAIService | None = None,
        dispatcher: ActionDispatcher | None = None,
        logger: IHistoryLogger | None = None
    ):
        # Todas as dependências são abstrações (interfaces):
        self.recorder = recorder or SoundDeviceRecorder()
        self.ai_service = ai_service or GeminiAIService()
        self.dispatcher = dispatcher or ActionDispatcher()
        self.logger = logger or MarkdownHistoryLogger()

    def finalizar_e_processar_voz(self) -> tuple[IntentResult, ActionResult]:
        audio_bytes = self.recorder.parar()
        intent = self.ai_service.processar_audio(audio_bytes)
        result = self.dispatcher.despachar(intent)
        self.logger.registrar(intent.transcription, intent.action, intent.params)
        return intent, result

    def processar_comando_texto(self, texto: str) -> tuple[IntentResult, ActionResult]:
        intent = self.ai_service.processar_texto(texto)
        result = self.dispatcher.despachar(intent)
        self.logger.registrar(intent.transcription, intent.action, intent.params)
        return intent, result
```

---

## 5. Modelos de Domínio e Contratos (core/)

### 5.1. Como Era no Código Legado:
**Inexistente**. O sistema transmitia dicionários genéricos `dict` onde qualquer chave podia estar ausente (`{"transcricao": ..., "acao": ...}`), gerando verificações defensivas espalhadas por toda a aplicação.

### 5.2. Como É Feito Agora:

#### A. Contratos Segregados: `AssistenteVoz_SOLID/core/interfaces.py` (ISP)
```python
# AssistenteVoz_SOLID/core/interfaces.py
@runtime_checkable
class IAudioRecorder(Protocol):
    def iniciar(self) -> None: ...
    def parar(self) -> bytes: ...
    def cancelar(self) -> None: ...
    def esta_gravando(self) -> bool: ...

@runtime_checkable
class IAIService(Protocol):
    def processar_audio(self, audio_bytes: bytes) -> IntentResult: ...
    def processar_texto(self, texto: str) -> IntentResult: ...

@runtime_checkable
class IActionHandler(Protocol):
    @property
    def nome_acao(self) -> str: ...
    def executar(self, parametros: dict[str, Any], contexto: IntentResult | None = None) -> ActionResult: ...

@runtime_checkable
class IHistoryLogger(Protocol):
    def registrar(self, texto: str, acao: str, detalhes: dict[str, Any]) -> None: ...
```

#### B. Modelos Tipados: `AssistenteVoz_SOLID/core/models.py` (LSP)
```python
# AssistenteVoz_SOLID/core/models.py
@dataclass
class IntentResult:
    transcription: str = ""
    action: str = "outro"
    params: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

@dataclass
class ActionResult:
    status: str
    saida: str = ""
    acao: str = ""
    comando: str = ""
    success: bool = True
```

---

## 6. Quadro Comparativo Geral

| Componente | O Que Fazia Antes | Como Fazia Antes | O Que Faz Agora | Como Faz Agora |
| :--- | :--- | :--- | :--- | :--- |
| **Interface Gráfica** | *God Class* (>730 linhas): UI, captura de som, requisição HTTP e execução de comandos. | `processar_audio()` e `executar_acao_estruturada()` disparados diretamente da thread do Tkinter. | *View* pura e desacoplada. | Recebe `VoiceAssistantController` injetado e apenas exibe resultados. |
| **Serviço de IA** | Acumulava hardware de som, parsing, HTTP e gravação em disco. | `GravadorAudio` e chamada silenciosa a `registrar_transcricao()` dentro de `gemini_service.py`. | Cliente REST puro e atômico. | Implementa `IAIService`, recebe áudio e devolve `IntentResult` tipado. |
| **Captura de Áudio** | Embutida dentro do arquivo de IA do Gemini. | `GravadorAudio` procedural com `sounddevice` e `scipy` em `gemini_service.py`. | Módulo independente de captura. | `SoundDeviceRecorder` implementa `IAudioRecorder` em `services/audio_recorder.py`. |
| **Execução de Ações** | Monólito com `if-elif-else` rígido e parsing léxico de strings no meio da execução. | `if acao == "abrir_navegador": ... elif acao == "executar_cmd": ...` em `actions.py`. | Padrão Command / Strategy extensível. | `ActionDispatcher` com handlers atômicos (`BrowserActionHandler`, `CmdActionHandler`, `AppLauncherHandler`). |
| **Persistência de Logs** | Misturada dentro de `actions.py` e chamada como efeito colateral em `gemini_service.py`. | `registrar_transcricao()` chamada internamente por quem não deveria. | Serviço de auditoria segregado. | `MarkdownHistoryLogger` orquestrado pelo `Controller`. |
| **Tipos e Contratos** | Ausentes. Transmissão baseada em strings e dicionários soltos (`dict`). | `dados.get("acao")` espalhado com fallbacks defensivos. | Modelos tipados e Protocolos formais. | `IntentResult` e `ActionResult` via `dataclass` e contratos `typing.Protocol`. |
