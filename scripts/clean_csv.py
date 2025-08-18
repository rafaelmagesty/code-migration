import pandas as pd
import re
import os
from glob import glob

# Função para extrair o código de um texto markdown
def extrair_codigo_markdown(texto):
    if pd.isna(texto):
        return ""
    
    # Expressão regular para encontrar o bloco <think>...</think>
    think_match = re.search(r"<think>.*?</think>", texto, re.DOTALL)
    if think_match:
        texto = texto[think_match.end():]
    
    # Expressão regular para capturar blocos de código Markdown
    matches = re.findall(r"```(?:\w*\s*)?\n?(.*?)```", texto, re.DOTALL)
    
    if matches:
        # Retorna o último bloco de código encontrado
        return matches[-1].strip()
    
    return texto.strip()

# --- Configurações de Caminho ---
pasta_entrada = "/home/rafaelmagesty/LLMs/code-migration/output"
pasta_saida = os.path.join(pasta_entrada, "processed_files")

# --- Cria a pasta de saída se ela não existir ---
if not os.path.exists(pasta_saida):
    os.makedirs(pasta_saida)
    print(f"Pasta de saída criada: {pasta_saida}")

# Encontra todos os arquivos CSV na pasta de entrada
csv_files = glob(os.path.join(pasta_entrada, "*.csv"))

# Processa cada arquivo
for arquivo_completo_entrada in csv_files:
    # Extrai o nome do arquivo e o nome do novo arquivo limpo
    nome_arquivo_base = os.path.basename(arquivo_completo_entrada)
    base_nome, extensao = os.path.splitext(nome_arquivo_base)
    nome_arquivo_limpo = f"{base_nome}_limpo{extensao}"
    
    # Monta o caminho completo para o arquivo de saída
    caminho_completo_saida = os.path.join(pasta_saida, nome_arquivo_limpo)
    
    # 📌 NOVO: VERIFICA SE O ARQUIVO DE SAÍDA JÁ EXISTE
    if os.path.exists(caminho_completo_saida):
        print(f"✅ Arquivo já processado. Pulando: {nome_arquivo_base}")
        continue
    
    print(f"Processando: {nome_arquivo_base}")
    try:
        # Lê o arquivo usando o caminho completo de entrada
        df = pd.read_csv(arquivo_completo_entrada)
        
        if 'migrated_code' in df.columns:
            df['migrated_code'] = df['migrated_code'].apply(extrair_codigo_markdown)
        else:
            print(f"⚠️ Coluna 'migrated_code' não encontrada em {nome_arquivo_base}, pulando.")
            continue
        
        # Salva o DataFrame processado no novo caminho
        df.to_csv(caminho_completo_saida, index=False)
        print(f"✅ Arquivo salvo: {caminho_completo_saida}")
    except Exception as e:
        print(f"❌ Erro ao processar {nome_arquivo_base}: {e}")