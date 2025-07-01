# models/base_client.py

import os
import re

class BaseClient:
    def load_template(self, file_name):
        # Assume que você guardou seus .txt em code-migration/templates/
        root = os.path.abspath(os.path.join(__file__, "..", ".."))
        path = os.path.join(root, "templates", f"{file_name}.txt")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def get_input_code(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return f"ERROR: File not found at '{file_path}'"
        except Exception as e:
            return f"ERROR: {e}"

    def find_pattern(self, formatted, flag):
        pattern = rf"{{{flag}}}(.*?)[\r\n]*{{{flag}_END}}"
        matches = re.findall(pattern, formatted, re.DOTALL)
        return matches

    def generate_request_dict(self, role, content):
        return {"role": role, "content": content}

    def generate_prompt(self, template: str, **kwargs) -> str:
        """
        Substitui apenas as chaves que estão em kwargs (ex: removed_chunk, commit_date),
        deixando intactas todas as outras marcações {SYSTEM_CONFIG}, {USER_CONFIG}, etc.
        """
        formatted = template
        for key, val in kwargs.items():
            formatted = formatted.replace(f"{{{key}}}", str(val))
        return formatted
