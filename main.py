import argparse
import os

from models.gpt_client import GPTClient
from models.ollama_client import OllamaClient
from pathlib import Path


def get_client_by_model(model_name):
    if model_name == "gpt":
        return GPTClient()
    elif model_name == "ollama":
        return OllamaClient()
    else:
        raise Exception(f"Unsupported model: {model_name}")


def save_result_to_file(input_path, language_name, model_name, result_content):
    try:
        path_obj = Path(input_path)

        repo_name = path_obj.parts[3]
        original_filename = path_obj.name

        output_dir = Path("output") / language_name / model_name / repo_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file_path = output_dir / original_filename
        output_file_path.write_text(result_content, encoding="utf-8")

        return str(output_file_path)

    except IndexError:
        return (
            f"ERRO: O caminho de entrada '{input_path}' não possui a estrutura esperada "
            f"de 'input/linguagem/biblioteca/repositorio/arquivo'."
        )
    except Exception as e:
        return f"Ocorreu um erro ao tentar salvar o arquivo: {e}"


def main():
    parser = argparse.ArgumentParser(description="Run code migration using GPT.")
    parser.add_argument("LANGUAGE_NAME", help="Programming language (e.g., python)")
    parser.add_argument("OLD_LIB_NAME", help="Original library name (e.g., boto)")
    parser.add_argument("NEW_LIB_NAME", help="New library name (e.g., boto3)")
    parser.add_argument("MODEL", help="Model family (e.g., gpt)")
    parser.add_argument("VERSION", help="Model version (e.g., gpt-4)")
    parser.add_argument("PROMPT", help="Prompt template (e.g., one_shot)")
    parser.add_argument(
        "INPUT_PATH", help="Input file path (e.g., input/python/boto/ex.txt)"
    )

    args = parser.parse_args()

    try:
        client = get_client_by_model(args.MODEL)
        result = client.process(args)
        saved_path = save_result_to_file(
            input_path=args.INPUT_PATH,
            language_name=args.LANGUAGE_NAME,
            model_name=args.MODEL,
            result_content=result,
        )
        print("\nMigração concluída com sucesso!")
        print(f"Resultado salvo em: {saved_path}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
