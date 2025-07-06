import os
import re

class BaseClient:
    def load_template(self, file_name):
        """
        Carrega o conteúdo de um arquivo de template.
        Assume que os templates estão em 'code-migration/templates/'.
        """
        # Constrói o caminho absoluto para o arquivo de template
        root = os.path.abspath(os.path.join(__file__, "..", ".."))
        path = os.path.join(root, "templates", f"{file_name}.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found at: {path}")
        except Exception as e:
            raise IOError(f"Error loading template {file_name}: {e}")

    def get_input_code(self, file_path):
        """
        Lê o conteúdo de um arquivo de código de entrada.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return f"ERROR: File not found at '{file_path}'"
        except Exception as e:
            return f"ERROR: {e}"

    def find_pattern(self, text, flag):
        """
        Encontra e retorna o conteúdo delimitado por {FLAG} e {FLAG_END} em um texto.
        """
        pattern = rf"{{{flag}}}(.*?){{{flag}_END}}"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    def generate_request_dict(self, role, content):
        """
        Gera um dicionário formatado para uma mensagem de chat.
        """
        return {"role": role, "content": content}

    def generate_prompt(self, template: str, **kwargs) -> str:
        """
        Substitui placeholders dinâmicos (como {removed_chunk}, {commit_date})
        no template, deixando as marcações de seção intactas.
        Valores string com chaves literais são escapados temporariamente.
        """
        formatted = template
        for key, val in kwargs.items():
            # Escapa chaves literais nos valores para evitar conflitos com .format()
            if isinstance(val, str):
                # Usa um padrão de escape temporário que não colide com chaves reais do template
                val = val.replace("{", "TEMP_OPEN_BRACE_").replace("}", "_TEMP_CLOSE_BRACE")
            
            # Substitui o placeholder no template
            formatted = formatted.replace(f"{{{key}}}", str(val))
        
        # Restaura as chaves literais nos valores após a substituição
        formatted = formatted.replace("TEMP_OPEN_BRACE_", "{").replace("_TEMP_CLOSE_BRACE", "}")
        return formatted