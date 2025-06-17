import ollama

from models.base_client import BaseClient


class OllamaClient(BaseClient):
    def __init__(self):
        self.client = ollama

    def generate_prompt(self, template, **kwargs):
        formatted = template.format(**kwargs)
        system_match = self.find_pattern(formatted, "SYSTEM_CONFIG")
        user_match = self.find_pattern(formatted, "USER_CONFIG")

        system_config = self.generate_request_dict("system", system_match[0])
        user_config_1 = self.generate_request_dict("user", user_match[0])

        if kwargs["PROMPT"] != "one_shot":
            return [system_config, user_config_1]

        assistant_match = self.find_pattern(formatted, "ASSISTANT_CONFIG")
        assistant_config = self.generate_request_dict("assistant", assistant_match[0])

        user_config_2 = self.generate_request_dict("user", user_match[1])

        return [system_config, user_config_1, assistant_config, user_config_2]

    def process(self, args):
        try:
            input_code = self.get_input_code(file_path=args.INPUT_PATH)
            template = self.load_template(file_name=args.PROMPT)
            prompt = self.generate_prompt(
                template=template,
                PROMPT=args.PROMPT,
                LANGUAGE_NAME=args.LANGUAGE_NAME,
                OLD_LIB_NAME=args.OLD_LIB_NAME,
                NEW_LIB_NAME=args.NEW_LIB_NAME,
                CODE_BEFORE_MIGRATION=input_code,
            )
            response = self.client.chat(model=args.VERSION, messages=prompt)
            return response["message"]["content"]
        except ValueError as e:
            return f"{self.__class__.__name__} could not generate a response: {e}"
