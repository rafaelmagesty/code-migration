# models/gemini_client.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

from models.base_client import BaseClient

# Carrega variáveis de ambiente de .env
load_dotenv()

class GeminiClient(BaseClient):
    def __init__(self):
        """
        Inicializa o cliente Gemini (Google Generative AI).
        Exige que exista a variável GOOGLE_API_KEY no .env.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Defina a variável GOOGLE_API_KEY no seu .env")
        genai.configure(api_key=api_key)

    def generate_prompt(self, template: str, **kwargs):
        """
        Formata o template e converte os blocos SYSTEM/USER/ASSISTANT
        em mensagens compatíveis com o Gemini (autor + conteúdo).
        """
        # BaseClient.generate_prompt retorna lista de dicts {"role":..., "content": ...}
        formatted_msgs = super().generate_prompt(template, **kwargs)

        # Renomeia 'role' → 'author' para a API do Gemini
        messages = []
        for msg in formatted_msgs:
            messages.append({
                "author":  msg["role"],    # 'system' | 'user' | 'assistant'
                "content": msg["content"]
            })
        return messages

    def process(self, args):
        """
        Executa o fluxo:
        1) Lê o trecho de código em args.INPUT_PATH (removed_chunk).
        2) Carrega o template args.PROMPT.
        3) Gera lista de mensagens Gemini.
        4) Chama genai.chat.create() com modelo args.VERSION.
        5) Retorna apenas o conteúdo da resposta.
        """
        # 1) captura o código (removed_chunk)
        snippet = self.get_input_code(file_path=args.INPUT_PATH)

        # 2) template a usar (one_shot, zero_shot, chain_of_thoughts)
        template = self.load_template(file_name=args.PROMPT)

        # 3) monta as mensagens para o Gemini
        messages = self.generate_prompt(
            template=template,
            PROMPT=args.PROMPT,
            removed_chunk=snippet,
            commit_date=args.COMMIT_DATE  # opcional, se seu template usar essa flag
        )

        # 4) invoca a API de chat do Gemini
        response = genai.chat.create(
            model=args.VERSION,   # ex: "gemini-1.5", "gemini-pro"
            messages=messages
        )

        # 5) devolve só o texto da última mensagem
        return response.last.message.content
