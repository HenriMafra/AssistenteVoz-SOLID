# Relatório de Diagnóstico SOLID: Assistente de Voz Windows

Este documento apresenta uma análise arquitetural aprofundada do projeto **AssistenteVoz** localizado em `C:\Users\henri.mafra\Downloads\AssistenteVoz`, confrontando a base de código atual com os **cinco princípios SOLID** detalhados no guia do [FreeCodeCamp: Os princípios SOLID da Programação Orientada a Objetos explicados em bom português](https://www.freecodecamp.org/portuguese/news/os-principios-solid-da-programacao-orientada-a-objetos-explicados-em-bom-portugues/).

---

## 1. Visão Geral do Diagnóstico

A aplicação atual é funcional e resolve o problema proposto (capturar voz, transcrever/interpretar via Gemini e executar comandos no Windows). No entanto, sua estrutura arquitetural é predominantemente **procedural e altamente acoplada**, com classes "God Object" na UI e funções que acumulam múltiplas responsabilidades.

| Princípio SOLID | Status no Projeto Atual | Nível de Risco / Débito Técnico |
| :--- | :--- | :--- |
| **S - Single Responsibility Principle** (Responsabilidade Única) | ❌ Violado em todos os módulos | **Crítico**: Classes e arquivos com 4 a 7 motivos distintos para mudar. |
| **O - Open/Closed Principle** (Aberto/Fechado) | ❌ Violado no despachante de ações e seleção de IA | **Alto**: Adicionar novas ações exige alterar blocos `if/elif` existentes. |
| **L - Liskov Substitution Principle** (Substituição de Liskov) | ⚠️ Comprometido por ausência de polimorfismo e retornos híbridos | **Médio**: Retornos heterogêneos (`CompletedProcess \| Popen`) e falso contrato em `ResultadoAcao`. |
| **I - Interface Segregation Principle** (Segregação de Interfaces) | ❌ Inexistente (ausência de contratos e interfaces tipadas) | **Médio**: Acoplamento a dicionários implícitos sem validação de tipos ou segregação de métodos. |
| **D - Dependency Inversion Principle** (Inversão de Dependência) | ❌ Violado (dependência direta de implementações concretas) | **Crítico**: UI e CLI instanciam e chamam diretamente APIs e hardware sem abstrações. |

---

## 2. Análise Detalhada Princípio a Princípio

### 2.1. [S] - Single Responsibility Principle (Princípio da Responsabilidade Única)

> *"Uma classe deve ter um, e apenas um, motivo para mudar."* — Robert C. Martin (Uncle Bob)

#### Violações Identificadas no Código

1. **[`gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/gemini_service.py)**:
   O módulo possui **7 responsabilidades distintas**:
   - Carregamento e inferência de variáveis de ambiente (`_carregar_env`).
   - Validação de chaves de API (`obter_api_token`).
   - Definição do prompt de engenharia da IA (`PROMPT_SISTEMA`).
   - Parsing e higienização de saída JSON com Regex (`extrair_json_resposta`).
   - Acesso e captura de hardware de áudio do microfone (`GravadorAudio`, `gravar_audio_interativo`, `gravar_audio_segundos`).
   - Chamadas HTTP REST ao endpoint do Google (`requests.post`).
   - Persistência em disco: o serviço de IA chama `registrar_transcricao()` internamente nas linhas 200 e 240, gerando um efeito colateral oculto de I/O em disco a cada inferência.

2. **[`actions.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/actions.py)**:
   - Mistura **execução de sistema operacional** (`abrir_navegador`, `executar_cmd`, `abrir_aplicativo`) com **persistência de histórico em Markdown** (`registrar_transcricao`).
   - Na função `executar_acao_estruturada` (linhas 111-140), o código executa o comando CMD em background para pegar o stdout, faz uma análise léxica na transcrição em português procurando por palavras como `"cmd"`, `"prompt"` ou `"terminal"`, e decide se abre uma segunda janela interativa. Essa análise léxica/semântica pertence à camada de interpretação, e não à de execução de comandos.

3. **[`app_gui.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/app_gui.py)** (`AssistenteVozGUI`):
   - É uma clássica **God Class** com mais de 730 linhas.
   - Gerencia: Widgets de UI (Tkinter), animação de ondas em Canvas, cronômetro de contagem regressiva, orquestração de threads (`threading.Thread`), controle de fluxo assíncrono, chamada direta da IA e execução direta de comandos no SO.
   - Se o formato de retorno da IA mudar, ou se a biblioteca de áudio mudar, a interface visual gráfica quebra e precisa ser alterada.

---

### 2.2. [O] - Open/Closed Principle (Princípio Aberto/Fechado)

> *"Entidades de software (classes, módulos, funções) devem estar abertas para extensão, mas fechadas para modificação."* — Bertrand Meyer

#### Violações Identificadas no Código

1. **Estrutura condicional monolítica em [`actions.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/actions.py#L95-L156)**:
   ```python
   def executar_acao_estruturada(dados: dict) -> ResultadoAcao:
       acao = dados.get("acao", "outro")
       if acao == "abrir_navegador":
           ...
       elif acao == "executar_cmd":
           ...
       elif acao == "abrir_aplicativo":
           ...
       return ResultadoAcao(...)
   ```
   **O Problema**: Para adicionar qualquer nova capacidade ao assistente (por exemplo, `ajustar_volume`, `tirar_screenshot`, `bloquear_tela`, `tocar_spotify`), o desenvolvedor é obrigado a abrir `actions.py` e modificar diretamente a função `executar_acao_estruturada`, correndo o risco de introduzir regressões nas ações já existentes e testadas.

2. **Engessamento dos modelos em [`gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/gemini_service.py#L186-L191)**:
   A lista de modelos com fallback `modelos = [modelo, "gemini-3.6-flash"]` está fixada no código procedural. Para suportar outro provedor (ex: Grok, OpenAI ou Claude) ou adicionar estratégias de retry customizadas, é preciso alterar a implementação interna da função.

#### Solução SOLID (Command / Strategy Pattern com Registro Aberto):
Criar uma interface base abstrata para ações e um `ActionRegistry` (ou Dispatcher). Novas ações são adicionadas criando novas classes e registrando-as, sem modificar nenhuma linha do despachante:

```python
from abc import ABC, abstractmethod

class IActionHandler(ABC):
    @property
    @abstractmethod
    def action_name(self) -> str:
        """Nome da ação correspondente retornado pela IA."""
        pass

    @abstractmethod
    def execute(self, params: dict) -> "CommandResult":
        """Executa a ação e retorna o resultado padronizado."""
        pass

class ActionDispatcher:
    def __init__(self):
        self._handlers: dict[str, IActionHandler] = {}

    def register(self, handler: IActionHandler) -> None:
        self._handlers[handler.action_name] = handler

    def dispatch(self, action_name: str, params: dict) -> "CommandResult":
        handler = self._handlers.get(action_name)
        if not handler:
            return CommandResult(success=False, output="Ação não suportada.")
        return handler.execute(params)
```

---

### 2.3. [L] - Liskov Substitution Principle (Princípio da Substituição de Liskov)

> *"Se para cada objeto o1 do tipo S há um objeto o2 do tipo T tal que, para todos os programas P definidos em termos de T, o comportamento de P não seja alterado quando o1 for substituído por o2, então S é um subtipo de T."* — Barbara Liskov

Como explicado no artigo do FreeCodeCamp com o exemplo clássico do Retângulo e Quadrado, uma subclasse ou implementação não pode alterar os contratos esperados ou quebrar comportamentos presumidos por quem a consome.

#### Violações e Inconsistências Identificadas no Código

1. **Falsa conformidade de dicionário em `ResultadoAcao` ([`actions.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/actions.py#L25-L41))**:
   ```python
   class ResultadoAcao:
       def __init__(self, status: str, saida: str = "", acao: str = "", comando: str = ""):
           ...
       def get(self, chave: str, padrao=None):
           return getattr(self, chave, padrao)
       def __getitem__(self, chave: str):
           return getattr(self, chave)
   ```
   **O Problema**: A classe tenta emular o comportamento de um dicionário (`__getitem__` e `get`), mas não implementa a interface `collections.abc.Mapping`. Não implementa `__contains__`, `keys()`, `values()`, `items()` nem `__iter__`. Qualquer consumidor que receba `ResultadoAcao` acreditando ser um mapeamento (`isinstance(obj, Mapping)` ou executando `for k, v in res.items()`) falhará em tempo de execução com `AttributeError`.

2. **Retorno polimórfico incoerente em `executar_cmd` ([`actions.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/actions.py#L53))**:
   ```python
   def executar_cmd(comando: str, interativo: bool = True) -> subprocess.CompletedProcess | subprocess.Popen:
   ```
   **O Problema**: A função retorna objetos de tipos e comportamentos completamente divergentes com base em um booleano:
   - Se `interativo=True`, retorna `subprocess.Popen` (processo em segundo plano ativo, sem atributos `stdout` populados imediatamente).
   - Se `interativo=False`, retorna `subprocess.CompletedProcess` (processo finalizado de forma síncrona).
   Isso força o chamador a fazer verificações do tipo `isinstance` ou `hasattr` (como feito na linha 117 de `actions.py`), violando a previsibilidade de contratos.

---

### 2.4. [I] - Interface Segregation Principle (Princípio da Segregação de Interface)

> *"Muitas interfaces específicas de clientes são melhores do que uma interface de propósito geral. Clientes não devem ser forçados a depender de métodos que não utilizam."* — Robert C. Martin

No artigo do FreeCodeCamp, isso é ilustrado pela interface `Estacionamento`: misturar cobrança e vagas em uma única interface força um estacionamento gratuito a implementar métodos financeiros inúteis.

#### Violações Identificadas no Código

1. **Acoplamento a Estruturas Não Segregadas (Dicionários Genéricos)**:
   Os componentes se comunicam através de um dicionário dinâmico genérico:
   `{"transcricao": ..., "acao": ..., "parametros": {...}, "explicacao": ...}`.
   - A camada de execução (`actions.py`) precisa apenas da tupla `(acao, parametros)`, mas recebe o dicionário inteiro com `transcricao` e faz parsing de texto dentro de si.
   - A camada de UI precisa apresentar dados formatados, mas precisa desempacotar manualmente chaves soltas usando `.get(...)` defensivo com fallbacks em vários pontos do código.
2. **Mistura de Gravação e Disparo em `GravadorAudio`**:
   O `GravadorAudio` acumula o papel de stream contínuo assíncrono e conversão de formato (`np.concatenate` + `wavfile.write` para WAV). Um cliente que só queira capturar amostras brutas (ex: para streaming em tempo real) é forçado a arcar com o processamento de WAV do `io.BytesIO`.

---

### 2.5. [D] - Dependency Inversion Principle (Princípio da Inversão de Dependência)

> *"Módulos de alto nível não devem depender de módulos de baixo nível. Ambos devem depender de abstrações. Abstrações não devem depender de detalhes. Detalhes devem depender de abstrações."* — Robert C. Martin

Este é o princípio com maior impacto estrutural no projeto.

#### Violações Identificadas no Código

1. **[`app_gui.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/app_gui.py#L9-L10) e [`main.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/main.py#L6-L13)**:
   Tanto a interface gráfica quanto a CLI importam diretamente as implementações de baixo nível:
   ```python
   from actions import executar_acao_estruturada
   from gemini_service import GravadorAudio, processar_audio, processar_texto, obter_api_token
   ```
   **O Problema**:
   - A GUI (módulo de apresentação de alto nível) depende diretamente de chamadas de rede HTTP ao Gemini (`requests`), captura de hardware (`sounddevice`), e comandos de terminal do Windows (`subprocess`).
   - Se você quiser testar a GUI, é obrigado a simular (`patch`) dezenas de chamadas nativas em testes unitários.
   - Se o backend de IA for substituído pela API do Grok (conforme o objetivo original do [`specs.md`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/specs.md): *"Objetivo: USAR API DO GROK..."*), a GUI precisará ser alterada.

2. **Acoplamento de Dependências em [`gemini_service.py`](file:///C:/Users/henri.mafra/Downloads/AssistenteVoz/gemini_service.py#L13)**:
   O serviço de IA importa `from actions import registrar_transcricao`.
   Ou seja, o serviço de inteligência artificial de nuvem depende de um módulo de automação local do Windows para gravar logs de arquivos! Essa inversão inadequada amarra dois módulos conceituais independentes.

---

## 3. Arquitetura: Comparativo Antes vs. Depois

```mermaid
flowchart TD
    subgraph Arquitetura Atual (Acoplada e Sem Abstrações)
        direction TB
        GUI_A[app_gui.py / AssistenteVozGUI]
        CLI_A[main.py / CLI]
        GEM_A[gemini_service.py]
        ACT_A[actions.py]
        LOG_A[(transcricao.md)]
        OS_A[Windows OS / CMD / Browser]

        GUI_A -->|Chama diretamente| GEM_A
        GUI_A -->|Chama diretamente| ACT_A
        CLI_A -->|Chama diretamente| GEM_A
        CLI_A -->|Chama diretamente| ACT_A
        GEM_A -->|Grava histórico| ACT_A
        ACT_A -->|Escreve em disco| LOG_A
        ACT_A -->|Executa subprocess| OS_A
    end
```

```mermaid
flowchart TD
    subgraph Arquitetura Refatorada com SOLID
        direction TB
        subgraph Apresentacao [Camada de Apresentação]
            GUI[AssistenteVozGUI]
            CLI[MainCLI]
        end

        subgraph Dominio_Contratos [Domínio & Abstrações - Interfaces]
            IAudioRecorder["<<interface>>\nIAudioRecorder"]
            IAIService["<<interface>>\nIAIService"]
            IActionHandler["<<interface>>\nIActionHandler"]
            IHistoryLogger["<<interface>>\nIHistoryLogger"]
        end

        subgraph CasosDeUso [Camada de Aplicação]
            AssistantController[VoiceAssistantController\n(Orquestrador)]
            ActionDispatcher[ActionDispatcher]
        end

        subgraph Infraestrutura [Infraestrutura & Implementações Concretas]
            SoundDeviceRecorder[SoundDeviceRecorder]
            GeminiAIService[GeminiAIService]
            GrokAIService[GrokAIService (Opcional)]
            MarkdownLogger[MarkdownHistoryLogger]
            BrowserHandler[BrowserActionHandler]
            CmdHandler[CmdActionHandler]
            AppHandler[AppLauncherActionHandler]
        end

        GUI --> AssistantController
        CLI --> AssistantController

        AssistantController --> IAudioRecorder
        AssistantController --> IAIService
        AssistantController --> ActionDispatcher
        AssistantController --> IHistoryLogger

        ActionDispatcher --> IActionHandler

        SoundDeviceRecorder -.->|Implementa| IAudioRecorder
        GeminiAIService -.->|Implementa| IAIService
        GrokAIService -.->|Implementa| IAIService
        MarkdownLogger -.->|Implementa| IHistoryLogger
        BrowserHandler -.->|Implementa| IActionHandler
        CmdHandler -.->|Implementa| IActionHandler
        AppHandler -.->|Implementa| IActionHandler
    end
```

---

## 4. Proposta de Código Refatorado (Antes vs. Depois)

### 4.1. Contratos e Entidades de Domínio (`core/interfaces.py` e `core/models.py`)

Em vez de dicionários soltos com chaves de strings mágicas, criamos estruturas de dados imutáveis e interfaces bem definidas:

```python
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

@dataclass(frozen=True)
class IntentResult:
    """Representa a intenção compreendida pela IA."""
    transcription: str
    action: str
    params: dict = field(default_factory=dict)
    explanation: str = ""

@dataclass(frozen=True)
class ActionResult:
    """Resultado inequívoco da execução de uma ação."""
    success: bool
    status: str
    output: str = ""
    action: str = ""

@runtime_checkable
class IAudioRecorder(Protocol):
    def start(self) -> None: ...
    def stop(self) -> bytes: ...
    def cancel(self) -> None: ...
    def is_recording(self) -> bool: ...

@runtime_checkable
class IAIService(Protocol):
    def process_audio(self, audio_bytes: bytes) -> IntentResult: ...
    def process_text(self, text: str) -> IntentResult: ...

@runtime_checkable
class IActionHandler(Protocol):
    @property
    def action_name(self) -> str: ...
    def execute(self, params: dict, context: IntentResult | None = None) -> ActionResult: ...

@runtime_checkable
class IHistoryLogger(Protocol):
    def log(self, intent: IntentResult, result: ActionResult) -> None: ...
```

---

### 4.2. Isolamento de Ações seguindo SRP e OCP (`actions/`)

Cada ação ganha sua própria classe com responsabilidade exclusiva:

```python
import subprocess
import urllib.parse
import webbrowser
from core.interfaces import IActionHandler
from core.models import ActionResult, IntentResult

class BrowserActionHandler(IActionHandler):
    @property
    def action_name(self) -> str:
        return "abrir_navegador"

    def execute(self, params: dict, context: IntentResult | None = None) -> ActionResult:
        query = (params.get("query") or params.get("url") or "").strip()
        if not query:
            return ActionResult(success=False, status="Busca vazia", action=self.action_name)

        if query.startswith(("http://", "https://")):
            url = query
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

        webbrowser.open(url)
        return ActionResult(
            success=True,
            status=f"Navegador aberto com: '{query}'",
            output=f"Pesquisa aberta: {url}",
            action=self.action_name
        )


class CmdActionHandler(IActionHandler):
    @property
    def action_name(self) -> str:
        return "executar_cmd"

    def execute(self, params: dict, context: IntentResult | None = None) -> ActionResult:
        comando = params.get("comando", "dir")
        try:
            res = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                encoding="cp850",
                errors="replace"
            )
            saida = res.stdout.strip() or res.stderr.strip() or "Comando executado com sucesso."
            return ActionResult(
                success=(res.returncode == 0),
                status=f"CMD executado com código {res.returncode}",
                output=saida,
                action=self.action_name
            )
        except Exception as e:
            return ActionResult(
                success=False,
                status=f"Falha ao executar CMD: {e}",
                output=str(e),
                action=self.action_name
            )
```

---

### 4.3. Despachante Aberto para Extensão (`services/action_dispatcher.py`)

O despachante não precisa ser modificado nunca mais:

```python
class ActionDispatcher:
    def __init__(self):
        self._handlers: dict[str, IActionHandler] = {}

    def register(self, handler: IActionHandler) -> "ActionDispatcher":
        self._handlers[handler.action_name] = handler
        return self

    def execute(self, intent: IntentResult) -> ActionResult:
        handler = self._handlers.get(intent.action)
        if not handler:
            return ActionResult(
                success=True,
                status="Nenhuma ação local executada.",
                output="Comando identificado como pergunta ou solicitação geral.",
                action=intent.action
            )
        return handler.execute(intent.params, context=intent)
```

---

### 4.4. Orquestrador de Aplicação com Inversão de Dependências (`services/controller.py`)

A lógica de negócio deixa a interface visual e passa para o controlador de casos de uso:

```python
class VoiceAssistantController:
    """Controlador que orquestra o fluxo sem conhecer detalhes visuais ou de SO."""
    def __init__(
        self,
        recorder: IAudioRecorder,
        ai_service: IAIService,
        dispatcher: ActionDispatcher,
        logger: IHistoryLogger
    ):
        self.recorder = recorder
        self.ai_service = ai_service
        self.dispatcher = dispatcher
        self.logger = logger

    def process_voice_command(self) -> tuple[IntentResult, ActionResult]:
        audio_bytes = self.recorder.stop()
        intent = self.ai_service.process_audio(audio_bytes)
        result = self.dispatcher.execute(intent)
        self.logger.log(intent, result)
        return intent, result

    def process_text_command(self, text: str) -> tuple[IntentResult, ActionResult]:
        intent = self.ai_service.process_text(text)
        result = self.dispatcher.execute(intent)
        self.logger.log(intent, result)
        return intent, result
```

**Benefício imediato para a GUI**:
A classe `AssistenteVozGUI` passa a receber `controller: VoiceAssistantController` em seu `__init__`. Ela apenas lida com cliques de botões e exibição de texto, reduzindo o seu tamanho e tornando-a 100% testável sem mocks complexos de subprocess ou requests.

---

## 5. Roteiro Prático de Refatoração Recomendado

1. **Fase 1 (Extração de Interfaces e Modelos)**:
   Criar `core/models.py` (`IntentResult`, `ActionResult`) e `core/interfaces.py` com `typing.Protocol` para `IAudioRecorder`, `IAIService`, `IActionHandler` e `IHistoryLogger`.
2. **Fase 2 (Segregação de Persistência e Ações)**:
   - Mover `registrar_transcricao` de `actions.py` para um serviço dedicado (`MarkdownHistoryLogger`).
   - Retirar chamadas de I/O em disco de dentro de `gemini_service.py`.
   - Quebrar as funções de `actions.py` em Handlers de ação (`BrowserActionHandler`, `CmdActionHandler`, `AppLauncherHandler`) e introduzir o `ActionDispatcher`.
3. **Fase 3 (Desacoplamento do Serviço de Áudio e IA)**:
   - Manter `GravadorAudio` em um arquivo específico (`services/audio_recorder.py`).
   - Fazer `GeminiService` implementar a interface `IAIService` sem tocar no microfone ou no disco.
4. **Fase 4 (Inversão de Dependências na GUI e CLI)**:
   - Criar `VoiceAssistantController` que conecta as partes.
   - Refatorar `AssistenteVozGUI` e `main.py` para receberem o controlador injetado.
5. **Fase 5 (Testes Unitários sem Monkey Patching)**:
   - Como tudo depende de interfaces, os testes unitários podem injetar mocks limpos ou implementações `Fake` em memória sem depender de patches invasivos em módulos globais do Python.
