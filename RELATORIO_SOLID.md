# Relatório Cirúrgico de Refatoração SOLID: Mapeamento de Linhas e Arquivos

Este relatório apresenta o **mapeamento exato de arquivos, números de linhas, códigos Antes vs. Depois e justificativas arquiteturais** da transformação realizada no projeto, fundamentado no artigo do [FreeCodeCamp: Os princípios SOLID da Programação Orientada a Objetos explicados em bom português](https://www.freecodecamp.org/portuguese/news/os-principios-solid-da-programacao-orientada-a-objetos-explicados-em-bom-portugues/).

---

## 1. Mapeamento Cirúrgico por Arquivo

---

### CASO 1: Desmantelamento da "God Class" (AssistenteVozGUI) e Chamada Direta do Gemini/SO na Interface
- **Arquivo Legado**: [`AssistenteVoz/app_gui.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/app_gui.py)
- **Anti-Pattern Identificado**: **God Class (ou God Object)** — Uma única classe acumulando mais de 730 linhas e 8 responsabilidades distintas.
- **Princípios Violados**: **SRP** (Responsabilidade Única) e **DIP** (Inversão de Dependência)
- **Novos Arquivos Refatorados**: [`AssistenteVoz_SOLID/ui/app_gui.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/ui/app_gui.py) e [`AssistenteVoz_SOLID/services/controller.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/controller.py)

#### Por Que Era uma "God Class"?
A classe `AssistenteVozGUI` centralizava praticamente todas as operações do sistema em um único lugar:
1. **Apresentação Visual**: Telas, layout, botões, caixas de texto e paletas Tkinter.
2. **Animação**: Loop de desenho das ondas sonoras no Canvas.
3. **Temporização**: Lógica do cronômetro de 12 segundos e cancelamento via `after()`.
4. **Concorrência**: Gerenciamento direto de `threading.Thread` e flags de estado (`processando`, `cancelado`).
5. **Captura de Hardware**: Instanciação física do microfone (`self.gravador = GravadorAudio()`).
6. **Comunicação de Rede**: Disparo de chamadas HTTP REST para a nuvem da Google Gemini.
7. **Execução no SO**: Invocação de processos `subprocess` e comandos do terminal CMD.
8. **Manipulação de Arquivos do SO**: Abertura direta do arquivo de log via `os.startfile` e Notepad.

#### Linhas e Código no Arquivo Legado (`AssistenteVoz/app_gui.py`)
1. **Linhas 9 e 10**:
   ```python
   # Importação direta de infraestrutura de baixo nível na camada de apresentação visual:
   from actions import executar_acao_estruturada, abrir_aplicativo
   from gemini_service import GravadorAudio, processar_audio, processar_texto, obter_api_token
   ```
2. **Linha 48**:
   ```python
   # Acoplamento rígido com hardware de áudio dentro do __init__ da janela Tkinter:
   self.gravador = GravadorAudio(samplerate=16000)
   ```
3. **Linhas 548 a 562** (Worker de áudio):
   ```python
   def _worker_processar_audio(self):
       try:
           wav_bytes = self.gravador.parar()
           if self.cancelado:
               return

           # [VIOLAÇÃO CRÍTICA]: A UI disparando requisição HTTP para a nuvem do Google Gemini:
           resultado = processar_audio(wav_bytes)
           if self.cancelado:
               return

           # [VIOLAÇÃO CRÍTICA]: A UI executando comandos CMD e processos do Windows:
           status = executar_acao_estruturada(resultado)
           if self.cancelado:
               return

           self.root.after(0, self._atualizar_sucesso, resultado, status)
   ```
4. **Linhas 624 a 636** (Worker de texto):
   ```python
   def _worker_processar_texto(self, comando: str):
       try:
           # [VIOLAÇÃO]: A UI chamando diretamente o modelo de linguagem:
           resultado = processar_texto(comando)
           if self.cancelado:
               return

           # [VIOLAÇÃO]: A UI executando comandos de terminal:
           status = executar_acao_estruturada(resultado)
           if self.cancelado:
               return

           self.root.after(0, self._atualizar_sucesso, resultado, status)
   ```

#### Como Foi Arrumado (`AssistenteVoz_SOLID`)
1. **No arquivo [`AssistenteVoz_SOLID/ui/app_gui.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/ui/app_gui.py)**:
   - **Linhas 15 a 17**: As importações de `gemini_service` e `actions` foram **removidas**. A GUI importa apenas o modelo de dados e o orquestrador:
     ```python
     from core.models import ActionResult, IntentResult
     from services.controller import VoiceAssistantController
     ```
   - **Linhas 24 a 28**: Injeção de dependência no `__init__`:
     ```python
     def __init__(self, root: tk.Tk, controller: VoiceAssistantController | None = None):
         self.root = root
         self.controller = controller or VoiceAssistantController()
     ```
   - **Linhas 545 a 555**: O worker de áudio delega tudo em uma única linha de intenção ao `Controller`:
     ```python
     def _worker_processar_audio(self):
         try:
             # A GUI não sabe quem grava, quem envia HTTP ou quem executa no SO:
             intent, status = self.controller.finalizar_e_processar_voz()
             if self.cancelado:
                 return
             self.root.after(0, self._atualizar_sucesso, intent, status)
     ```
   - **Linhas 585 a 595**: O worker de texto delega igualmente:
     ```python
     def _worker_processar_texto(self, comando: str):
         try:
             intent, status = self.controller.processar_comando_texto(comando)
             if self.cancelado:
                 return
             self.root.after(0, self._atualizar_sucesso, intent, status)
     ```
2. **No arquivo [`AssistenteVoz_SOLID/services/controller.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/controller.py)** (Linhas 42 a 55):
   A regra de negócio e orquestração fica centralizada na camada de aplicação através de interfaces abstratas (`IAudioRecorder`, `IAIService`, `IActionHandler`, `IHistoryLogger`).

---

### CASO 2: Monólito de IA com Hardware, Regex, HTTP e Gravação em Disco no Mesmo Módulo
- **Arquivo Legado**: [`AssistenteVoz/gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/gemini_service.py)
- **Princípios Violados**: **SRP** (Responsabilidade Única), **ISP** (Segregação de Interfaces) e **DIP** (Inversão de Dependência)
- **Novos Arquivos Refatorados**:
  - [`AssistenteVoz_SOLID/services/audio_recorder.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/audio_recorder.py)
  - [`AssistenteVoz_SOLID/services/gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/gemini_service.py)
  - [`AssistenteVoz_SOLID/services/history_logger.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/history_logger.py)

#### Linhas e Código no Arquivo Legado (`AssistenteVoz/gemini_service.py`)
1. **Linha 13**:
   ```python
   # [VIOLAÇÃO SRP/DIP]: O cliente de IA importando persistência do módulo de ações locais:
   from actions import registrar_transcricao
   ```
2. **Linhas 88 a 143** (`class GravadorAudio`):
   ```python
   # [VIOLAÇÃO SRP]: Toda a lógica de microfone físico, buffers NumPy, sounddevice e conversão WAV
   # estava implementada DENTRO do arquivo do cliente de IA Gemini:
   class GravadorAudio:
       def __init__(self, samplerate: int = 16000): ...
       def _callback(self, indata, frames, time_info, status): ...
       def iniciar(self) -> None: ...
       def parar(self) -> bytes: ...
   ```
3. **Linhas 146 a 164**:
   Funções procedurais de captura de microfone via console (`gravar_audio_interativo` e `gravar_audio_segundos`) misturadas com código de rede.
4. **Linhas 200 a 204** (Dentro de `processar_audio`) e **Linhas 239 a 243** (Dentro de `processar_texto`):
   ```python
   # [VIOLAÇÃO SRP]: Efeito colateral oculto de escrita em disco a cada inferência:
   registrar_transcricao(
       texto=resultado.get("transcricao", ""),
       acao=resultado.get("acao", "outro"),
       detalhes=resultado.get("parametros", {})
   )
   ```

#### Como Foi Arrumado (`AssistenteVoz_SOLID`)
1. **Captura de Áudio Isolada**:
   - Movida para [`services/audio_recorder.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/audio_recorder.py) (Linhas 11 a 75).
   - Implementa o contrato [`IAudioRecorder`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/interfaces.py#L12) definido em [`core/interfaces.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/interfaces.py).
   - O serviço de IA agora não precisa mais importar `sounddevice`, `scipy` ou `numpy`.
2. **Cliente de IA Puro (Sem Efeito Colateral de Disco)**:
   - Em [`services/gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/gemini_service.py) (Linhas 97 a 195), a classe [`GeminiAIService`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/gemini_service.py#L97) implementa [`IAIService`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/interfaces.py#L35).
   - Ela recebe dados, consulta a API e devolve um [`IntentResult`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/models.py#L9). **Não escreve nada no disco**.
3. **Persistência Isolada**:
   - Em [`services/history_logger.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/history_logger.py) (Linhas 32 a 55), [`MarkdownHistoryLogger`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/history_logger.py#L32) implementa [`IHistoryLogger`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/interfaces.py#L60).
   - O orquestrador (`VoiceAssistantController`) decide quando e onde gravar, sem acoplar a IA à persistência.

---

### CASO 3: Despachante Monolítico com `if-elif-else` e Parsing Léxico no Executor
- **Arquivo Legado**: [`AssistenteVoz/actions.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/actions.py)
- **Princípios Violados**: **OCP** (Aberto/Fechado), **SRP** (Responsabilidade Única) e **LSP** (Substituição de Liskov)
- **Novos Arquivos Refatorados**:
  - [`AssistenteVoz_SOLID/actions/base.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/base.py)
  - [`AssistenteVoz_SOLID/actions/browser.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/browser.py)
  - [`AssistenteVoz_SOLID/actions/cmd.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/cmd.py)
  - [`AssistenteVoz_SOLID/actions/app.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/app.py)
  - [`AssistenteVoz_SOLID/actions/dispatcher.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/dispatcher.py)

#### Linhas e Código no Arquivo Legado (`AssistenteVoz/actions.py`)
1. **Linhas 25 a 41** (`class ResultadoAcao`):
   ```python
   # [VIOLAÇÃO LSP]: Falso mapeamento. Tentava fingir que era dicionário com __getitem__,
   # mas quebrava com iteradores, keys() ou verificação isinstance(obj, Mapping):
   class ResultadoAcao:
       def __init__(self, status: str, saida: str = "", acao: str = "", comando: str = ""): ...
       def get(self, chave: str, padrao=None): ...
       def __getitem__(self, chave: str): ...
   ```
2. **Linhas 53 a 65** (`executar_cmd`):
   ```python
   # [VIOLAÇÃO LSP]: Retornava tipos incompatíveis com base em parâmetro booleano:
   def executar_cmd(comando: str, interativo: bool = True) -> subprocess.CompletedProcess | subprocess.Popen:
   ```
3. **Linhas 75 a 93** (`registrar_transcricao`):
   ```python
   # [VIOLAÇÃO SRP]: Gravação de arquivo Markdown misturada com execução de SO:
   def registrar_transcricao(texto: str, acao: str, detalhes: dict, arquivo: str = "transcricao.md") -> None:
   ```
4. **Linhas 95 a 155** (`executar_acao_estruturada`):
   ```python
   # [VIOLAÇÃO OCP]: Estrutura condicional rígida. Impossível adicionar nova ação sem modificar este arquivo:
   def executar_acao_estruturada(dados: dict) -> ResultadoAcao:
       acao = dados.get("acao", "outro")
       params = dados.get("parametros", {})
       transcricao = dados.get("transcricao", "").lower()

       if acao == "abrir_navegador":
           ...
       elif acao == "executar_cmd":
           # [VIOLAÇÃO SRP]: Análise léxica de palavras em português na camada de execução:
           if "cmd" in transcricao or "prompt" in transcricao or "terminal" in transcricao or "abrir" in transcricao:
               executar_cmd(comando, interativo=True)
           ...
       elif acao == "abrir_aplicativo":
           ...
   ```

#### Como Foi Arrumado (`AssistenteVoz_SOLID`)
1. **Substituição de Liskov Garantida**:
   - Em [`core/models.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/models.py) (Linhas 46 a 89), [`ActionResult`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/core/models.py#L46) implementa contrato imutável, suporte seguro a `__getitem__`, `get()`, propriedades de compatibilidade e exportação para dicionário `to_dict()`.
2. **Aberto/Fechado (OCP) com Command / Strategy**:
   - Em [`actions/dispatcher.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/dispatcher.py) (Linhas 16 a 55), [`ActionDispatcher`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/dispatcher.py#L16) registra handlers via `registrar_handler(handler: IActionHandler)`.
   - **Nenhuma linha de `ActionDispatcher` precisa ser alterada** para incluir novas ações no assistente.
3. **Handlers Atômicos (SRP)**:
   - [`actions/browser.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/browser.py) (Linhas 23 a 48): [`BrowserActionHandler`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/browser.py#L23) cuida unicamente de navegação web.
   - [`actions/cmd.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/cmd.py) (Linhas 32 a 65): [`CmdActionHandler`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/cmd.py#L32) cuida unicamente de subprocessos.
   - [`actions/app.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/app.py) (Linhas 32 a 52): [`AppLauncherHandler`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/actions/app.py#L32) cuida unicamente de executáveis do Windows.

---

### CASO 4: Inversão de Dependência na Linha de Comando (CLI)
- **Arquivo Legado**: [`AssistenteVoz/main.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/main.py)
- **Princípio Violado**: **DIP** (Inversão de Dependência)
- **Novo Arquivo Refatorado**: [`AssistenteVoz_SOLID/main.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/main.py)

#### Linhas e Código no Arquivo Legado (`AssistenteVoz/main.py`)
1. **Linhas 6 a 13**:
   Importações diretas de funções procedurais de baixo nível.
2. **Linhas 58 a 74** e **Linhas 88 a 98**:
   O `main.py` duplicava manualmente todo o pipeline de execução:
   `gravar_audio -> processar_audio -> print -> executar_acao_estruturada`.
   Essa duplicação significava que qualquer ajuste no fluxo precisava ser replicado tanto na GUI quanto na CLI.

#### Como Foi Arrumado (`AssistenteVoz_SOLID/main.py`)
- **Linha 14**: Importa [`VoiceAssistantController`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz_SOLID/services/controller.py#L18).
- **Linhas 31 a 40**: A CLI recebe o `controller` e apenas solicita a execução de alto nível, mantendo paridade arquitetural absoluta com a GUI.

---

## 2. Tabela Resumo das Linhas Afetadas

| Arquivo Original | Linhas Originais com Problema | O que foi arrumado | Novos Componentes / Arquivos de Destino |
| :--- | :--- | :--- | :--- |
| `app_gui.py` | **Linhas 9-10, 48, 548-562, 624-636** | **God Class** (>730 linhas) misturando UI, threads, rede e SO | `ui/app_gui.py`: UI pura desacoplada delegando para `VoiceAssistantController` |
| `gemini_service.py`| **Linha 13** | Dependência de `registrar_transcricao` | `services/gemini_service.py`: Depende apenas de `core/interfaces.py` |
| `gemini_service.py`| **Linhas 88-143** | Classe `GravadorAudio` acumulada no serviço de IA | `services/audio_recorder.py` (Linhas 11-75): `SoundDeviceRecorder` |
| `gemini_service.py`| **Linhas 200-204** | Efeito colateral de gravação em disco | `services/gemini_service.py` (Linhas 97-150): Inferência pura |
| `actions.py` | **Linhas 25-41** | `ResultadoAcao` com falso mapeamento | `core/models.py` (Linhas 46-89): `ActionResult` tipado |
| `actions.py` | **Linhas 75-93** | `registrar_transcricao` no módulo de SO | `services/history_logger.py` (Linhas 12-55): `MarkdownHistoryLogger` |
| `actions.py` | **Linhas 95-155** | Encadeamento `if-elif-else` monolítico | `actions/dispatcher.py` (Linhas 16-55): Padrão Command / Strategy |
| `actions.py` | **Linhas 129-133** | Parsing léxico de strings durante a execução | `actions/cmd.py` (Linhas 32-65): Execução isolada |
| `main.py` | **Linhas 58-98** | Duplicação do pipeline procedural de orquestração | `main.py` (Linhas 31-50): Delegado ao `VoiceAssistantController` |

---

## 3. Conclusão da Especificidade

Todas as violações apontadas foram corrigidas cirurgicamente, comprovadas por **18 testes automatizados (100% de aprovação)** e versionadas de ponta a ponta no repositório GitHub [AssistenteVoz-SOLID](https://github.com/HenriMafra/AssistenteVoz-SOLID).
