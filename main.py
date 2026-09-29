"""Ponto de entrada para Execução via Linha de Comando (CLI).

Permite interagir pelo terminal ou passar comandos pontuais via flags,
utilizando o VoiceAssistantController com injeção de dependências.
"""
import argparse
import sys
from pathlib import Path

from actions import executar_acao_estruturada
from gemini_service import (
    gravar_audio_interativo,
    gravar_audio_segundos,
    processar_audio,
    processar_texto,
    obter_api_token
)
from services.controller import VoiceAssistantController

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def exibir_cabecalho() -> None:
    print("=" * 60)
    print("      [ASSISTENTE DE VOZ PARA ACOES NO WINDOWS]")
    print("        Powered by Gemini Flash IA (SOLID Architecture)")
    print("=" * 60)


def loop_interativo(controller: VoiceAssistantController | None = None) -> None:
    ctrl = controller or VoiceAssistantController()
    exibir_cabecalho()

    if not ctrl.verificar_conexao():
        print("[ERRO] Erro de autenticacao: Chave da API do Gemini nao configurada no .env")
        return
    print("[OK] Chave da API do Gemini carregada com sucesso do ambiente.")

    while True:
        print("\nEscolha uma opcao:")
        print("  [1] Falar no microfone (Pressione ENTER para iniciar e finalizar)")
        print("  [2] Falar por 5 segundos (Gravacao cronometrada)")
        print("  [3] Digitar comando em texto (Teste sem microfone)")
        print("  [4] Ver historico de transcricoes (transcricao.md)")
        print("  [0] Sair")

        opcao = input("\nOpcao: ").strip()

        if opcao == "0":
            print("\nEncerrando assistente. Ate logo!")
            break

        elif opcao in ("1", "2"):
            try:
                if opcao == "1":
                    audio_bytes = gravar_audio_interativo()
                else:
                    audio_bytes = gravar_audio_segundos(segundos=5)

                print("\n[IA] Transcrevendo audio e interpretando intencao...")
                resultado = processar_audio(audio_bytes)

                print("\n" + "-" * 50)
                print(f"Transcricao : {resultado.get('transcricao', '')}")
                print(f"Acao        : {resultado.get('acao', '')}")
                print(f"Detalhes    : {resultado.get('parametros', {})}")
                print(f"Explicacao  : {resultado.get('explicacao', '')}")
                print("-" * 50)

                status = executar_acao_estruturada(resultado)
                print(f"Status de Execucao: {status}")

            except KeyboardInterrupt:
                print("\nOperacao cancelada pelo usuario.")
            except Exception as erro:
                print(f"\n[ERRO] Durante o processamento do audio: {erro}")

        elif opcao == "3":
            comando = input("\nDigite o que deseja fazer (ex: 'abra o google e pesquise sobre python'): ").strip()
            if not comando:
                print("Comando vazio.")
                continue

            try:
                print("\n[IA] Interpretando intencao...")
                resultado = processar_texto(comando)

                print("\n" + "-" * 50)
                print(f"Entrada    : {resultado.get('transcricao', '')}")
                print(f"Acao       : {resultado.get('acao', '')}")
                print(f"Detalhes   : {resultado.get('parametros', {})}")
                print(f"Explicacao : {resultado.get('explicacao', '')}")
                print("-" * 50)

                status = executar_acao_estruturada(resultado)
                print(f"Status de Execucao: {status}")

            except Exception as erro:
                print(f"\n[ERRO] Durante o processamento do texto: {erro}")

        elif opcao == "4":
            caminho_md = Path("transcricao.md")
            if caminho_md.exists():
                print("\n" + "=" * 50)
                print(caminho_md.read_text(encoding="utf-8"))
                print("=" * 50)
            else:
                print("\nNenhuma transcrição foi gravada ainda.")

        else:
            print("Opção inválida. Tente novamente.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assistente de Voz e Ações Locais no Windows com Gemini Flash")
    parser.add_argument("--texto", "-t", type=str, help="Executa diretamente um comando de texto")
    parser.add_argument("--segundos", "-s", type=int, help="Grava voz por N segundos e executa imediatamente")
    args = parser.parse_args()

    if args.texto:
        exibir_cabecalho()
        print(f"\n[Modo Direto] Processando texto: '{args.texto}'")
        res = processar_texto(args.texto)
        print(f"Ação detectada: {res.get('acao')}")
        status = executar_acao_estruturada(res)
        print(f"Resultado: {status}")
        return

    if args.segundos:
        exibir_cabecalho()
        audio = gravar_audio_segundos(segundos=args.segundos)
        res = processar_audio(audio)
        print(f"Transcrição: {res.get('transcricao')}")
        print(f"Ação: {res.get('acao')}")
        status = executar_acao_estruturada(res)
        print(f"Resultado: {status}")
        return

    loop_interativo()


if __name__ == "__main__":
    main()
