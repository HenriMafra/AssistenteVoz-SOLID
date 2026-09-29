# 🎙️ Assistente de Voz para Windows — Arquitetura SOLID

Microsolução modular em Python que captura comandos de voz do usuário, interpreta intenções em linguagem natural através do modelo **Gemini Flash**, persiste histórico e executa ações automatizadas no Windows.

Esta versão foi completamente arquitetada e refatorada aplicando os **cinco princípios SOLID** da Engenharia de Software Orientada a Objetos, conforme fundamentado no artigo do [FreeCodeCamp: Os princípios SOLID da Programação Orientada a Objetos explicados em bom português](https://www.freecodecamp.org/portuguese/news/os-principios-solid-da-programacao-orientada-a-objetos-explicados-em-bom-portugues/).

---

## 🏛️ Arquitetura Orientada a SOLID

A aplicação divide-se em camadas claras e com responsabilidades estritamente delimitadas:

```mermaid
flowchart TD
    subgraph Apresentacao [Camada de Apresentação]
        GUI[app_gui.py / Tkinter GUI]
        CLI[main.py / CLI Console]
    end

    subgraph Core [Domínio e Contratos - core/]
        Models[models.py\nIntentResult, ActionResult]
        Interfaces[interfaces.py\nIAudioRecorder, IAIService,\nIActionHandler, IHistoryLogger]
    end

    subgraph Aplicacao [Camada de Aplicação - services/]
        Controller[VoiceAssistantController\n(Orquestrador DIP)]
        Dispatcher[ActionDispatcher\n(Padrão Command / OCP)]
    end

    subgraph Infraestrutura [Infraestrutura e Hardware]
        AudioRec[SoundDeviceRecorder\n(sounddevice)]
        GeminiAPI[GeminiAIService\n(Google Gemini REST)]
        History[MarkdownHistoryLogger\n(transcricao.md)]
        OSActions[BrowserActionHandler\nCmdActionHandler\nAppLauncherHandler]
    end

    GUI --> Controller
    CLI --> Controller

    Controller --> Interfaces
    Controller --> Dispatcher
    Dispatcher --> OSActions

    AudioRec -.->|implementa| Interfaces
    GeminiAPI -.->|implementa| Interfaces
    History -.->|implementa| Interfaces
    OSActions -.->|implementa| Interfaces
```

### Os 5 Princípios no Projeto:

1. **S - Single Responsibility Principle (Responsabilidade Única)**:
   - Captura de áudio isolada em `services/audio_recorder.py`.
   - Comunicação com a API do Gemini isolada em `services/gemini_service.py`.
   - Persistência de arquivos Markdown isolada em `services/history_logger.py`.
   - Cada ação do sistema operacional possui seu próprio manipulador independente em `actions/`.
   - A interface gráfica (`ui/app_gui.py`) atua exclusivamente como visualizador e receptor de eventos.

2. **O - Open/Closed Principle (Aberto/Fechado)**:
   - O despachante `ActionDispatcher` implementa o padrão *Command / Strategy*. Para adicionar uma nova capacidade (ex: ajustar volume ou tirar screenshot), basta registrar uma nova classe sem nunca editar código existente.

3. **L - Liskov Substitution Principle (Substituição de Liskov)**:
   - Resultados de ações utilizam o contrato imutável e previsível `ActionResult`, que garante compatibilidade uniforme com acessos de atributos e chaves sem quebrar contratos de tipo.

4. **I - Interface Segregation Principle (Segregação de Interfaces)**:
   - Contratos definidos em `core/interfaces.py` usando `typing.Protocol` (`IAudioRecorder`, `IAIService`, `IActionHandler`, `IHistoryLogger`), garantindo que nenhum cliente seja forçado a depender de métodos que não utiliza.

5. **D - Dependency Inversion Principle (Inversão de Dependência)**:
   - O caso de uso `VoiceAssistantController` depende exclusivamente de interfaces abstratas, permitindo alternar de provedor de IA (ex: do Gemini para o Grok) ou de microfone sem alterar a UI ou a lógica de negócio.

---

## 🚀 Como Executar

### 1. Pré-requisitos e Instalação

Clone o repositório e crie um ambiente virtual:

```bash
# Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar chave de API
copy .env.example .env
# Edite o arquivo .env e insira sua GEMINI_API_TOKEN
```

### 2. Interface Gráfica (Recomendado)

```bash
python app_gui.py
```
- Interface moderna, responsiva com visualização de ondas sonoras e retorno imediato da execução local.

### 3. Modo Terminal / Linha de Comando (CLI)

```bash
# Modo menu interativo
python main.py

# Modo direto por texto
python main.py --texto "abra o google e pesquise sobre inteligência artificial"

# Modo direto por gravação de N segundos
python main.py --segundos 5
```

---

## 🧪 Testes Automatizados

A suíte de testes cobre tanto os testes de regressão originais quanto os testes estruturais dos princípios SOLID:

```bash
pytest -v
```

Testes inclusos:
- `test_assistant.py`: Testes unitários das ações no SO.
- `test_gemini_service.py`: Testes de parsing e comunicação com a IA.
- `test_gui.py`: Testes da interface gráfica em Tkinter com mocks.
- `test_main.py`: Testes dos argumentos de linha de comando.
- `test_solid.py`: Validação empírica de OCP, LSP, DIP e SRP com stubs desacoplados.

---

## 📂 Comparativo Detalhado

Para ver a comparação linha a linha entre a versão anterior e a versão refatorada, consulte o arquivo [COMPARATIVO_SOLID.md](COMPARATIVO_SOLID.md).
