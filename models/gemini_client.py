# models/gemini_client.py

import os
from dotenv import load_dotenv
import google.generativeai as genai # <-- Nova importação
from string import Template
from models.base_client import BaseClient # Assumindo que esta classe existe e tem find_pattern

load_dotenv()

class GeminiClient(BaseClient):
    def __init__(self):
        # Para o Google AI SDK, geralmente usamos uma API Key
        # Ou, se for para usar via Vertex AI (mais complexo), a autenticação é automática
        # se GOOGLE_APPLICATION_CREDENTIALS estiver configurado e o projeto estiver inicializado
        
        # Tentaremos configurar via API Key primeiro, que é o mais comum para uso "local"
        # Se você estiver usando o Vertex AI e tiver GOOGLE_APPLICATION_CREDENTIALS configurado,
        # o SDK do Google AI pode tentar usar essa credencial automaticamente para alguns modelos,
        # mas é mais robusto definir a API Key para uso direto.
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            # Fallback para credenciais de serviço se não houver API Key
            # Isso é mais comum com a abordagem do Vertex AI, que não usa API Key diretamente para o modelo.
            sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not sa_path or not os.path.isfile(sa_path):
                raise RuntimeError(
                    "Defina GEMINI_API_KEY OU GOOGLE_APPLICATION_CREDENTIALS (apontando para o JSON da Service Account)"
                )
            # A autenticação será feita automaticamente pelo ambiente com GOOGLE_APPLICATION_CREDENTIALS
            # Não precisamos chamar genai.configure_api_key() explicitamente.
            # No entanto, a classe ChatModel não existe aqui, usaremos o genai.GenerativeModel
        
        genai.configure(api_key=gemini_api_key)


    def generate_prompt(self, template: str, **kwargs) -> list[dict]:
        """
        Extrai os blocos SYSTEM_CONFIG, USER_CONFIG e ASSISTANT_CONFIG do template,
        preenche com kwargs usando string.Template e retorna lista de mensagens.
        """
        # encontra trechos
        system_raw = self.find_pattern(template, "SYSTEM_CONFIG")
        user_raw = self.find_pattern(template, "USER_CONFIG")
        assist_raw = self.find_pattern(template, "ASSISTANT_CONFIG")

        if not system_raw or not user_raw:
            raise ValueError("Template mal formado: faltam SYSTEM_CONFIG ou USER_CONFIG")
        
        system_tpl = system_raw[0]
        user_tpl = user_raw[0]
        assistant_tpl = assist_raw[0] if assist_raw else None

        # usa string.Template para não confundir chaves literais
        sys_msg = Template(system_tpl).safe_substitute(**kwargs)
        usr_msg = Template(user_tpl).safe_substitute(**kwargs)

        messages = []

        # O Google AI SDK (`google-generativeai`) lida com o "role" diretamente em seu método chat.
        # O "system" message (contexto) é passado separadamente ou incorporado na primeira mensagem do usuário se for um chat simples.
        # Para um chat "multi-turn", as mensagens precisam alternar entre 'user' e 'model' (não 'assistant').
        
        # Adiciona a mensagem do sistema como parte do histórico inicial se necessário
        if sys_msg:
            # No SDK genai, o 'system' role é mais sobre instruções de setup inicial,
            # ou parte do contexto de um chat. Para simplicidade, vamos incluir no histórico
            # como um 'user' message que estabelece o tom, ou considerar que o 'context'
            # no prompt já cumpre essa função.
            # Uma forma comum é adicionar instruções de sistema à primeira mensagem do usuário
            # ou manter o 'system_context' separado para ser usado na configuração do chat.
            # Para este SDK, o chat é mais direto: user -> model -> user -> model.
            # O "system" message seria mais como um "preamble" ou "context" na conversa.
            # Vamos tratar o system_msg como um setup inicial que pode ser parte do prompt do user.
            # No entanto, para ser fiel ao seu template, vamos adaptar:
            messages.append({"role": "user", "content": f"INSTRUÇÕES: {sys_msg}"})


        if assistant_tpl:
            ast_msg = Template(assistant_tpl).safe_substitute(**kwargs)
            # No google.generativeai, o role para o assistente é 'model'
            messages.append({"role": "model", "content": ast_msg})
        
        messages.append({"role": "user", "content": usr_msg})

        return messages

    def chat(self, *, model: str, messages: list[dict]) -> str:
        """
        Envia as mensagens para o Gemini usando o Google AI SDK (google.generativeai)
        e retorna apenas o texto da resposta.
        """
        # O Google AI SDK espera um histórico de mensagens que alterna 'user' e 'model'.
        # O 'system_context' não é um 'role' separado no histórico de chat para este SDK,
        # mas sim uma parte implícita do setup ou da primeira mensagem do usuário.
        
        # Criar uma lista de histórico no formato que o genai.GenerativeModel.start_chat espera
        # Ele espera [{"role": "user", "parts": ["..."]}, {"role": "model", "parts": ["..."]}, ...]
        
        # Processar as mensagens do seu formato para o formato do genai
        formatted_history = []
        for msg in messages:
            if msg["role"] == "system":
                # Se houver uma mensagem de sistema, ela pode ser tratada como a primeira instrução do usuário
                # ou pre-processada de alguma forma. Para simplificar, vou incorporá-la
                # ou assumir que o 'context' é passado de outra forma.
                # No genai, instruções de sistema geralmente vão no prompt inicial ou nos exemplos.
                # Para seu template, vamos ignorar o "role: system" aqui para o histórico de chat
                # e esperar que as instruções relevantes já estejam no prompt do usuário ou no setup.
                # Se o 'system_context' realmente precisar ser enviado, ele deve ser parte do primeiro turno 'user'.
                if msg["content"].startswith("INSTRUÇÕES:"):
                     # Se já adicionamos no generate_prompt, trataremos como parte do histórico do usuário
                    formatted_history.append({"role": "user", "parts": [msg["content"]]})
                continue # Pula para a próxima, já que 'system' não é um role direto no chat history
            
            # Mapeia 'assistant' para 'model'
            role = 'model' if msg["role"] == 'assistant' else msg["role"]
            formatted_history.append({"role": role, "parts": [msg["content"]]})

        # O último item em formatted_history deve ser a mensagem do usuário que queremos enviar agora
        # E o restante é o histórico.
        
        # Se o `formatted_history` tiver apenas uma mensagem (a do usuário atual), é um chat de um turno.
        # Se tiver mais, é um chat multi-turn.
        
        # Instancia o modelo
        # Note: 'model' aqui será 'gemini-pro', 'gemini-pro-vision', etc.
        gemini_model = genai.GenerativeModel(model)

        # Inicia o chat com o histórico. O `start_chat` do genai aceita um `history`.
        # O último item do `formatted_history` é o prompt atual do usuário.
        # O `start_chat` espera o histórico ANTES da sua próxima pergunta.
        
        # Separa o último prompt do usuário do histórico para enviar separadamente
        user_current_prompt = formatted_history[-1]["parts"][0]
        conversation_history = formatted_history[:-1] # Tudo menos o último item

        chat = gemini_model.start_chat(history=conversation_history)
        
        # Envia a mensagem mais recente do usuário
        response = chat.send_message(user_current_prompt)
        
        # A resposta pode ter múltiplas "parts", mas você quer o texto
        return response.text