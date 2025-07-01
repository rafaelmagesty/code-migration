import ollama
from models.base_client import BaseClient

class OllamaClient(BaseClient):
    def __init__(self):
        self.client = ollama

    def generate_prompt(self, template: str, **kwargs):
        # usa o replace só das vars que passamos
        formatted = super().generate_prompt(template, **kwargs)

        # extrai blocos
        system = self.find_pattern(formatted, "SYSTEM_CONFIG")[0]
        user1  = self.find_pattern(formatted, "USER_CONFIG")[0]

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user1},
        ]

        # para one_shot
        if kwargs.get("PROMPT") == "one_shot":
            assistant = self.find_pattern(formatted, "ASSISTANT_CONFIG")[0]
            user2     = self.find_pattern(formatted, "USER_CONFIG")[1]
            messages += [
                {"role": "assistant", "content": assistant},
                {"role": "user",      "content": user2},
            ]

        return messages

    def process(self, args):
        snippet  = self.get_input_code(file_path=args.INPUT_PATH)
        template = self.load_template(file_name=args.PROMPT)
        messages = self.generate_prompt(
            template=template,
            PROMPT=args.PROMPT,
            removed_chunk=snippet,
            commit_date=args.COMMIT_DATE
        )
        resp = self.client.chat(model=args.VERSION, messages=messages)
        return resp["message"]["content"]
