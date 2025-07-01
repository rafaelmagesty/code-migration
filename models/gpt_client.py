import os
from openai import OpenAI
from dotenv import load_dotenv

from models.base_client import BaseClient

load_dotenv()

class GPTClient(BaseClient):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Defina OPENAI_API_KEY no seu .env")
        self.client = OpenAI(api_key=api_key)

    def generate_prompt(self, template, **kwargs):
        # usa o replace seguro do BaseClient
        formatted = super().generate_prompt(template, **kwargs)

        system = self.find_pattern(formatted, "SYSTEM_CONFIG")[0]
        user   = self.find_pattern(formatted, "USER_CONFIG")[0]
        msgs = [
            self.generate_request_dict("system", system),
            self.generate_request_dict("user",   user)
        ]

        if kwargs.get("PROMPT") == "one_shot":
            assistant = self.find_pattern(formatted, "ASSISTANT_CONFIG")[0]
            user2     = self.find_pattern(formatted, "USER_CONFIG")[1]
            msgs += [
                self.generate_request_dict("assistant", assistant),
                self.generate_request_dict("user",      user2)
            ]

        return msgs

    def process(self, args):
        snippet  = self.get_input_code(file_path=args.INPUT_PATH)
        template = self.load_template(file_name=args.PROMPT)
        messages = self.generate_prompt(
            template=template,
            PROMPT=args.PROMPT,
            removed_chunk=snippet,
            commit_date=args.COMMIT_DATE
        )
        resp = self.client.chat.completions.create(
            model=args.VERSION, messages=messages
        )
        return resp.choices[0].message.content
