import pandas as pd
import os
import Levenshtein

# 1. Defina os caminhos dos arquivos de entrada e saída
CAMINHO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
CAMINHO_DESENVOLVEDOR_CSV = os.path.join(CAMINHO_BASE, "input", "todas_as_migracoes_unificadas.csv")
CAMINHO_LLM_CSV = os.path.join(CAMINHO_BASE, "output", "processed_files", "all_migrated_ollama_codellama_chain_of_thoughts_limpo.csv")
CAMINHO_RESULTADO = os.path.join(CAMINHO_BASE, "scripts", "metrics_results_levenshtein_only.csv") # Nome do arquivo alterado

# 2. Carregue os DataFrames
try:
    df_desenvolvedor = pd.read_csv(CAMINHO_DESENVOLVEDOR_CSV)
    df_llm = pd.read_csv(CAMINHO_LLM_CSV)
    print("✅ CSVs do desenvolvedor e da LLM lidos com sucesso!")
except FileNotFoundError as e:
    print(f"❌ Erro: Arquivo não encontrado. Verifique o caminho: {e}")
    exit()

# 3. Combinação dos DataFrames por Índice de Linha
print("\n🔄 Combinando DataFrames pela ordem das linhas (índice)...")

df_desenvolvedor = df_desenvolvedor.rename(columns={'added_chunk': 'codigo_desenvolvedor'})
df_llm = df_llm.rename(columns={'migrated_code': 'codigo_llm'})

df_dev_essencial = df_desenvolvedor[['codigo_desenvolvedor']]
df_llm_essencial = df_llm[['commit_hash', 'codigo_llm']]

df_dev_essencial = df_dev_essencial.reset_index(drop=True)
df_llm_essencial = df_llm_essencial.reset_index(drop=True)

if len(df_dev_essencial) != len(df_llm_essencial):
    print(f"⚠️ Atenção: O arquivo do desenvolvedor tem {len(df_dev_essencial)} linhas e o da LLM tem {len(df_llm_essencial)} linhas.")
    print("O DataFrame combinado terá o tamanho do menor arquivo, descartando as linhas excedentes.")

df_combined = pd.concat([df_llm_essencial, df_dev_essencial], axis=1)
df_combined.dropna(inplace=True)
df_combined = df_combined.reset_index(drop=True)

print(f"✅ DataFrames combinados. {len(df_combined)} entradas prontas para análise.")

# 4. Prepare a lista para armazenar a métrica
levenshtein_distances = []
erros_processamento = []

# 5. Itere sobre cada linha para calcular a métrica
for index, row in df_combined.iterrows():
    migrated_code_dev = str(row['codigo_desenvolvedor'])
    migrated_code_llm = str(row['codigo_llm'])
    commit_hash = row['commit_hash']

    # --- Cálculo do Levenshtein ---
    try:
        if not migrated_code_dev.strip() or not migrated_code_llm.strip():
            print(f"⚠️ Ignorando linha {index} do commit {commit_hash} devido a código vazio.")
            levenshtein_distances.append(None)
        else:
            distance = Levenshtein.distance(migrated_code_dev, migrated_code_llm)
            levenshtein_distances.append(distance)
    except Exception as e:
        print(f"❌ Erro inesperado no Levenshtein para o commit {commit_hash}: {e}")
        levenshtein_distances.append(None)
        erros_processamento.append(commit_hash)

# 6. Adicione a nova coluna ao DataFrame combinado
df_combined['levenshtein_distance'] = levenshtein_distances

# 7. Salve o DataFrame final em um novo CSV
try:
    df_combined.to_csv(CAMINHO_RESULTADO, index=False)
    print(f"\n✅ Análise de métricas concluída! Resultados salvos em: {CAMINHO_RESULTADO}")
    if erros_processamento:
        print(f"⚠️ Houve erros ao processar os seguintes commits: {list(set(erros_processamento))}")
except Exception as e:
    print(f"❌ Erro ao salvar o arquivo de resultados: {e}")