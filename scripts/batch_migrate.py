#!/usr/bin/env python3
import argparse
import pandas as pd
from models.gpt_client import GPTClient
from models.ollama_client import OllamaClient
from models.gemini_client import GeminiClient
import os

def get_client(model_name: str):
    model_name = model_name.lower()
    if model_name == "gpt":
        return GPTClient()
    if model_name == "ollama":
        return OllamaClient()
    if model_name == "gemini":
        return GeminiClient()
    raise ValueError(f"Modelo desconhecido: {model_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch code migration: do CSV(input) → CSV(output)"
    )
    parser.add_argument(
        "--input-csv", "-i",
        required=True,
        help="caminho para CSV de entrada (coluna removed_chunk)"
    )
    parser.add_argument(
        "--output-csv", "-o",
        default="out.csv",
        help="caminho para CSV de saída"
    )
    parser.add_argument(
        "--model", "-m",
        choices=["gpt","ollama", "gemini"],
        required=True,
        help="qual backend usar (gpt ou ollama)"
    )
    parser.add_argument(
        "--version", "-v",
        required=True,
        help="versão do modelo (ex: gpt-4, llama2)"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        choices=["one_shot","zero_shot","chain_of_thoughts"],
        help="qual template usar"
    )
    args = parser.parse_args()

    # 1) Carrega o CSV
    df = pd.read_csv(args.input_csv, encoding="utf-8", quoting=1, engine="python")
    if "removed_chunk" not in df.columns:
        raise SystemExit("⚠️ Coluna 'removed_chunk' não encontrada no CSV de entrada.")
    # commit_date é opcional: se faltar, usamos string vazia
    has_date = "commit_date" in df.columns

    # 2) Prepara cliente e template
    client = get_client(args.model)
    template = client.load_template(args.prompt)

    # 3) Para cada linha, gera o prompt e chama a LLM
    migrated = []
    total = len(df)
    for i, row in df.iterrows():
        chunk = row["removed_chunk"]
        date  = row["commit_date"] if has_date else ""
        # monta as mensagens (system + user (+assistant, se one_shot))
        messages = client.generate_prompt(
            template,
            commit_date   = date,
            removed_chunk = chunk
        )
        # chama a API
        try:
            if args.model == "gpt":
                resp = client.client.chat.completions.create(
                    model    = args.version,
                    messages = messages
                )
                out = resp.choices[0].message.content
            else:  # ollama
                resp = client.client.chat(
                    model    = args.version,
                    messages = messages
                )
                out = resp["message"]["content"]
        except Exception as e:
            out = f"ERROR: {e}"
        print(f"[{i+1}/{total}] → ok")
        migrated.append(out)

    # 4) Escreve CSV de saída
    # 3) adiciona ao DataFrame
    df["migrated_code"] = migrated

    df_out = df[["removed_chunk", "migrated_code", "commit_date"]]


    out_dir = os.path.dirname(args.output_csv)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    df_out.to_csv(args.output_csv, index=False, encoding="utf-8")

if __name__ == "__main__":
    main()
