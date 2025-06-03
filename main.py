import argparse

from models.gpt_client import GPTClient
from models.ollama_client import OllamaClient

def get_client_by_model(model_name):
    if model_name == "gpt":
        return GPTClient()
    elif model_name == "ollama":
        return OllamaClient()
    else:
        raise Exception(f"Unsupported model: {model_name}")
    
def main():
    parser = argparse.ArgumentParser(description="Run code migration using GPT.")
    parser.add_argument("LANGUAGE_NAME", help="Programming language (e.g., python)")
    parser.add_argument("OLD_LIB_NAME", help="Original library name (e.g., boto)")
    parser.add_argument("NEW_LIB_NAME", help="New library name (e.g., boto3)")
    parser.add_argument("MODEL", help="Model family (e.g., gpt)")
    parser.add_argument("VERSION", help="Model version (e.g., gpt-4)")
    parser.add_argument("PROMPT", help="Prompt template (e.g., one-shot)")

    args = parser.parse_args()

    try:
        client = get_client_by_model(args.MODEL)
        result = client.process(args)
        print(result)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
