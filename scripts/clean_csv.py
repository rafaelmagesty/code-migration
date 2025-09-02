import pandas as pd
import re
import os
from glob import glob
from typing import List

# Função para extrair o código de um texto markdown
def extrair_codigo_markdown_e_monitorar(texto: str, log_nao_capturados: List[str]) -> str:
    """
    Extrai o código de um texto markdown e registra casos não capturados.
    
    Args:
        texto (str): O texto da célula.
        log_nao_capturados (List[str]): Uma lista para registrar os textos não capturados.
        
    Returns:
        str: O código extraído ou o texto original se não for capturado.
    """
    if pd.isna(texto):
        return ""
    
    # 1. Tenta remover o bloco <think>
    think_match = re.search(r"<think>.*?</think>", texto, re.DOTALL)
    if think_match:
        texto_limpo = texto[think_match.end():]
    else:
        texto_limpo = texto
    
    # 2. Tenta capturar o bloco de código
    matches = re.findall(r"```(?:\w*\s*)?\n?(.*?)```", texto_limpo, re.DOTALL)
    
    if matches:
        # Retorna o último bloco de código encontrado
        return matches[-1].strip()
    else:
        # 3. Se nenhum bloco for encontrado, loga o texto original
        log_nao_capturados.append(texto)
        # Retorna a string original, mas sem espaços extras
        return texto_limpo.strip()

def processar_arquivos_csv(pasta_entrada: str, pasta_saida: str) -> None:
    """
    Processa arquivos CSV, limpa a coluna 'migrated_code' e salva
    os resultados e os casos não capturados em arquivos separados.
    """
    # Cria a pasta de saída se ela não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"Pasta de saída criada: {pasta_saida}")

    # Encontra todos os arquivos CSV na pasta de entrada
    csv_files = glob(os.path.join(pasta_entrada, "*.csv"))

    # Variável para armazenar todos os registros não capturados de todos os arquivos
    nao_capturados_geral = []

    # Processa cada arquivo
    for arquivo_completo_entrada in csv_files:
        # Extrai o nome do arquivo e o nome do novo arquivo limpo
        nome_arquivo_base = os.path.basename(arquivo_completo_entrada)
        base_nome, extensao = os.path.splitext(nome_arquivo_base)
        nome_arquivo_limpo = f"{base_nome}_limpo{extensao}"
        
        # Monta o caminho completo para o arquivo de saída
        caminho_completo_saida = os.path.join(pasta_saida, nome_arquivo_limpo)
        
        # Verifica se o arquivo de saída já existe
        if os.path.exists(caminho_completo_saida):
            print(f"✅ Arquivo já processado. Pulando: {nome_arquivo_base}")
            continue
        
        print(f"Processando: {nome_arquivo_base}")
        try:
            # Cria uma lista temporária para os casos não capturados deste arquivo
            log_nao_capturados = []
            df = pd.read_csv(arquivo_completo_entrada)
            
            if 'migrated_code' in df.columns:
                # Aplica a função de limpeza e monitoramento
                df['migrated_code'] = df['migrated_code'].apply(
                    lambda x: extrair_codigo_markdown_e_monitorar(x, log_nao_capturados)
                )
                
                # Adiciona os casos não capturados deste arquivo à lista geral
                nao_capturados_geral.extend(log_nao_capturados)
                
                print(f"📦 Foram encontrados {len(log_nao_capturados)} casos não capturados em {nome_arquivo_base}.")
            else:
                print(f"⚠️ Coluna 'migrated_code' não encontrada em {nome_arquivo_base}, pulando.")
                continue
            
            # Salva o DataFrame processado no novo caminho
            df.to_csv(caminho_completo_saida, index=False)
            print(f"✅ Arquivo salvo: {caminho_completo_saida}")
        except Exception as e:
            print(f"❌ Erro ao processar {nome_arquivo_base}: {e}")

    # --- Bloco de código para salvar os casos não capturados ---
    if nao_capturados_geral:
        # Cria um DataFrame a partir da lista de textos não capturados
        df_nao_capturados = pd.DataFrame(nao_capturados_geral, columns=['texto_original_nao_capturado'])
        
        # Define o caminho de saída para este novo arquivo
        caminho_saida_nao_capturados = os.path.join(pasta_saida, "casos_nao_capturados.csv")
        
        # Salva o DataFrame
        df_nao_capturados.to_csv(caminho_saida_nao_capturados, index=False)
        
        print(f"\n✅ Total de {len(nao_capturados_geral)} casos não capturados salvos em: {caminho_saida_nao_capturados}")
    else:
        print("\n✅ Nenhum caso não capturado foi encontrado em nenhum dos arquivos processados.")

# --- Execução do Script ---
if __name__ == "__main__":
    # Configure os caminhos das pastas de entrada e saída
    pasta_de_entrada = "/home/rafaelmagesty/LLMs/code-migration/output"
    pasta_de_saida_processados = os.path.join(pasta_de_entrada, "processed_files")

    processar_arquivos_csv(pasta_de_entrada, pasta_de_saida_processados)