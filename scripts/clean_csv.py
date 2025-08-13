import pandas as pd
import re
import os
from glob import glob

# Função para extrair o código de um texto markdown
def extrair_codigo_markdown(texto):
    if pd.isna(texto):
        return ""
    
    # Expressão regular para encontrar o bloco <think>...</think>
    # re.DOTALL é importante para que o '.' case com quebras de linha dentro do bloco
    think_match = re.search(r"<think>.*?</think>", texto, re.DOTALL)
    if think_match:
        # Se encontrou o bloco <think>, pega o texto *depois* dele
        texto = texto[think_match.end():]
    # --- FIM NOVO ---
    
    # Expressão regular para capturar blocos de código Markdown
    # Ela busca por:
    # 1. Três acentos graves (```)
    # 2. Opcionalmente, um nome de linguagem (ex: javascript) e/ou espaços (\w*\s*)
    # 3. Opcionalmente, uma quebra de linha (\n?)
    # 4. O conteúdo do código (.*?) - o '?' 
    # 5. Os três acentos graves de fechamento (```)
    # re.DOTALL é crucial para que o '.' capture quebras de linha
    
    # Usamos re.findall para pegar todas as ocorrências de blocos de código
    matches = re.findall(r"```(?:\w*\s*)?\n?(.*?)```", texto, re.DOTALL)
    
    if matches:
        # Retorna o último bloco de código encontrado
        return matches[-1].strip()
    
    # Se não encontrar nenhum bloco de código Markdown, retorna o texto original (limpo de espaços)
    return texto.strip()

pasta_entrada = "/home/rafaelmagesty/LLMs/code-migration/output"  

# Caminho COMPLETO da nova subpasta onde os arquivos CSV PROCESSADOS serão salvos
pasta_saida = os.path.join(pasta_entrada, "processed_files")   

# --- Cria a pasta de saída se ela não existir ---
if not os.path.exists(pasta_saida):
    os.makedirs(pasta_saida)
    print(f"Pasta de saída criada: {pasta_saida}")


# Encontra todos os arquivos CSV na pasta de entrada
csv_files = glob(os.path.join(pasta_entrada, "*.csv"))

# Processa cada arquivo
for arquivo_completo_entrada in csv_files:
    # Extrai apenas o nome do arquivo (ex: "meu_arquivo.csv") do caminho completo
    nome_arquivo_base = os.path.basename(arquivo_completo_entrada)
    print(f"Processando: {nome_arquivo_base}")
    try:
        # Lê o arquivo usando o caminho completo de entrada
        df = pd.read_csv(arquivo_completo_entrada)
        
        if 'migrated_code' in df.columns:
            df['migrated_code'] = df['migrated_code'].apply(extrair_codigo_markdown)
        else:
            print(f"⚠️ Coluna 'migrated_code' não encontrada em {nome_arquivo_base}, pulando.")
            continue
        
        # Cria o nome do novo arquivo (ex: "meu_arquivo_limpo.csv")
        base_nome, extensao = os.path.splitext(nome_arquivo_base)
        nome_arquivo_limpo = f"{base_nome}_limpo{extensao}"
        
        # Monta o caminho completo para salvar o arquivo na pasta de saída
        caminho_completo_saida = os.path.join(pasta_saida, nome_arquivo_limpo)
        
        # Salva o DataFrame processado no novo caminho
        df.to_csv(caminho_completo_saida, index=False)
        print(f"✅ Arquivo salvo: {caminho_completo_saida}")
    except Exception as e:
        print(f"Erro ao processar {nome_arquivo_base}: {e}")