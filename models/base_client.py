import re

class BaseClient():
    def load_template(self, file_name):
        path = f"models/templates/{file_name}.txt"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def find_pattern(self, formatted, flag):
        pattern = fr"{{{flag}}}(.*?)[\r\n]*{{{flag}_END}}"
        matches = re.findall(pattern, formatted, re.DOTALL)
        return matches
    
    def generate_request_dict(self, role, content):
        return {"role": role, "content": content}
    
    def generate_prompt(self, template, **kwargs):
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")