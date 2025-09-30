import pandas as pd
import os
from codebleu import calc_codebleu

# 1. Defina os caminhos dos arquivos de entrada e saída
CAMINHO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
CAMINHO_DESENVOLVEDOR_CSV = os.path.join(CAMINHO_BASE, "input", "todas_as_migracoes_unificadas.csv")
CAMINHO_LLM_CSV = os.path.join(CAMINHO_BASE, "output", "processed_files", "all_migrated_ollama_codellama_chain_of_thoughts_limpo.csv")
CAMINHO_RESULTADO = os.path.join(CAMINHO_BASE, "scripts", "metrics_results_codebleu_only.csv") # Apenas CodeBLEU

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

# Incluir código original (antes da migração) dos dois DataFrames
df_dev_essencial = df_desenvolvedor[['codigo_desenvolvedor']]
df_llm_essencial = df_llm[['commit_hash', 'codigo_llm']]

# Adicionar código original - verificar se existe nos DataFrames
codigo_original_col = None
if 'removed_chunk' in df_desenvolvedor.columns:
    codigo_original_col = 'removed_chunk'
    print("✅ Código original encontrado na coluna 'removed_chunk' do arquivo do desenvolvedor")
elif 'original_code' in df_llm.columns:
    codigo_original_col = 'original_code'
    print("✅ Código original encontrado na coluna 'original_code' do arquivo da LLM")
elif 'code_to_migrate' in df_llm.columns:
    codigo_original_col = 'code_to_migrate'
    print("✅ Código original encontrado na coluna 'code_to_migrate' do arquivo da LLM")
else:
    print("❌ ERRO: Não foi possível encontrar uma coluna com o código original.")
    print("Colunas disponíveis no arquivo do desenvolvedor:", list(df_desenvolvedor.columns))
    print("Colunas disponíveis no arquivo da LLM:", list(df_llm.columns))
    exit()

# Adicionar código original ao DataFrame essencial apropriado
if codigo_original_col in df_desenvolvedor.columns:
    df_dev_essencial = df_desenvolvedor[['codigo_desenvolvedor', codigo_original_col]]
    df_dev_essencial = df_dev_essencial.rename(columns={codigo_original_col: 'codigo_original'})
elif codigo_original_col in df_llm.columns:
    df_llm_essencial = df_llm[['commit_hash', 'codigo_llm', codigo_original_col]]
    df_llm_essencial = df_llm_essencial.rename(columns={codigo_original_col: 'codigo_original'})

df_dev_essencial = df_dev_essencial.reset_index(drop=True)
df_llm_essencial = df_llm_essencial.reset_index(drop=True)

if len(df_dev_essencial) != len(df_llm_essencial):
    print(f"⚠️ Atenção: O arquivo do desenvolvedor tem {len(df_dev_essencial)} linhas e o da LLM tem {len(df_llm_essencial)} linhas.")
    print("O DataFrame combinado terá o tamanho do menor arquivo, descartando as linhas excedentes.")

df_combined = pd.concat([df_llm_essencial, df_dev_essencial], axis=1)
df_combined.dropna(inplace=True)
df_combined = df_combined.reset_index(drop=True)

print(f"✅ DataFrames combinados. {len(df_combined)} entradas prontas para análise.")

# 4. Prepare as listas para armazenar todas as métricas CodeBLEU
# LLM vs Desenvolvedor
codebleu_llm_vs_dev = []
ngram_match_llm_vs_dev = []
weighted_ngram_match_llm_vs_dev = []
syntax_match_llm_vs_dev = []
dataflow_match_llm_vs_dev = []

# Original vs LLM
codebleu_original_vs_llm = []
ngram_match_original_vs_llm = []
weighted_ngram_match_original_vs_llm = []
syntax_match_original_vs_llm = []
dataflow_match_original_vs_llm = []

# Original vs Desenvolvedor
codebleu_original_vs_dev = []
ngram_match_original_vs_dev = []
weighted_ngram_match_original_vs_dev = []
syntax_match_original_vs_dev = []
dataflow_match_original_vs_dev = []

erros_processamento = []

# 5. Itere sobre cada linha para calcular as métricas CodeBLEU
for index, row in df_combined.iterrows():
    migrated_code_dev = str(row['codigo_desenvolvedor'])
    migrated_code_llm = str(row['codigo_llm'])
    codigo_original = str(row['codigo_original'])
    commit_hash = row['commit_hash']

    # --- Cálculo das métricas CodeBLEU ---
    try:
        # Verificar se algum código está vazio
        if not migrated_code_dev.strip() or not migrated_code_llm.strip() or not codigo_original.strip():
            print(f"⚠️ Ignorando linha {index} do commit {commit_hash} devido a código vazio.")
            # LLM vs Dev
            codebleu_llm_vs_dev.append(None)
            ngram_match_llm_vs_dev.append(None)
            weighted_ngram_match_llm_vs_dev.append(None)
            syntax_match_llm_vs_dev.append(None)
            dataflow_match_llm_vs_dev.append(None)
            # Original vs LLM
            codebleu_original_vs_llm.append(None)
            ngram_match_original_vs_llm.append(None)
            weighted_ngram_match_original_vs_llm.append(None)
            syntax_match_original_vs_llm.append(None)
            dataflow_match_original_vs_llm.append(None)
            # Original vs Dev
            codebleu_original_vs_dev.append(None)
            ngram_match_original_vs_dev.append(None)
            weighted_ngram_match_original_vs_dev.append(None)
            syntax_match_original_vs_dev.append(None)
            dataflow_match_original_vs_dev.append(None)
        else:
            # === SIMILARIDADE DE CÓDIGO ===
            # Limpar e preparar os códigos
            clean_migrated_dev = migrated_code_dev.strip()
            clean_migrated_llm = migrated_code_llm.strip()
            clean_original = codigo_original.strip()
            
            # Verificar se os códigos não estão vazios após limpeza
            if not clean_migrated_dev or not clean_migrated_llm or not clean_original:
                print(f"⚠️ Código vazio após limpeza para commit {commit_hash}")
                # LLM vs Dev
                codebleu_llm_vs_dev.append(None)
                ngram_match_llm_vs_dev.append(None)
                weighted_ngram_match_llm_vs_dev.append(None)
                syntax_match_llm_vs_dev.append(None)
                dataflow_match_llm_vs_dev.append(None)
                # Original vs LLM
                codebleu_original_vs_llm.append(None)
                ngram_match_original_vs_llm.append(None)
                weighted_ngram_match_original_vs_llm.append(None)
                syntax_match_original_vs_llm.append(None)
                dataflow_match_original_vs_llm.append(None)
                # Original vs Dev
                codebleu_original_vs_dev.append(None)
                ngram_match_original_vs_dev.append(None)
                weighted_ngram_match_original_vs_dev.append(None)
                syntax_match_original_vs_dev.append(None)
                dataflow_match_original_vs_dev.append(None)
                continue
            
            # 1. Similaridade entre código migrado pela LLM e pelo desenvolvedor
            try:
                codebleu_result_llm_vs_dev = calc_codebleu([clean_migrated_dev], [clean_migrated_llm], lang="javascript")
                codebleu_llm_vs_dev.append(codebleu_result_llm_vs_dev['codebleu'])
                ngram_match_llm_vs_dev.append(codebleu_result_llm_vs_dev['ngram_match_score'])
                weighted_ngram_match_llm_vs_dev.append(codebleu_result_llm_vs_dev['weighted_ngram_match_score'])
                syntax_match_llm_vs_dev.append(codebleu_result_llm_vs_dev['syntax_match_score'])
                dataflow_match_llm_vs_dev.append(codebleu_result_llm_vs_dev['dataflow_match_score'])
            except Exception as e:
                print(f"❌ Erro no CodeBLEU (LLM vs Dev) para o commit {commit_hash}: {e}")
                codebleu_llm_vs_dev.append(None)
                ngram_match_llm_vs_dev.append(None)
                weighted_ngram_match_llm_vs_dev.append(None)
                syntax_match_llm_vs_dev.append(None)
                dataflow_match_llm_vs_dev.append(None)
            
            # 2. Similaridade entre código original e código migrado pela LLM
            try:
                codebleu_result_original_vs_llm = calc_codebleu([clean_original], [clean_migrated_llm], lang="javascript")
                codebleu_original_vs_llm.append(codebleu_result_original_vs_llm['codebleu'])
                ngram_match_original_vs_llm.append(codebleu_result_original_vs_llm['ngram_match_score'])
                weighted_ngram_match_original_vs_llm.append(codebleu_result_original_vs_llm['weighted_ngram_match_score'])
                syntax_match_original_vs_llm.append(codebleu_result_original_vs_llm['syntax_match_score'])
                dataflow_match_original_vs_llm.append(codebleu_result_original_vs_llm['dataflow_match_score'])
            except Exception as e:
                print(f"❌ Erro no CodeBLEU (Original vs LLM) para o commit {commit_hash}: {e}")
                codebleu_original_vs_llm.append(None)
                ngram_match_original_vs_llm.append(None)
                weighted_ngram_match_original_vs_llm.append(None)
                syntax_match_original_vs_llm.append(None)
                dataflow_match_original_vs_llm.append(None)
            
            # 3. Similaridade entre código original e código migrado pelo desenvolvedor
            try:
                codebleu_result_original_vs_dev = calc_codebleu([clean_original], [clean_migrated_dev], lang="javascript")
                codebleu_original_vs_dev.append(codebleu_result_original_vs_dev['codebleu'])
                ngram_match_original_vs_dev.append(codebleu_result_original_vs_dev['ngram_match_score'])
                weighted_ngram_match_original_vs_dev.append(codebleu_result_original_vs_dev['weighted_ngram_match_score'])
                syntax_match_original_vs_dev.append(codebleu_result_original_vs_dev['syntax_match_score'])
                dataflow_match_original_vs_dev.append(codebleu_result_original_vs_dev['dataflow_match_score'])
            except Exception as e:
                print(f"❌ Erro no CodeBLEU (Original vs Dev) para o commit {commit_hash}: {e}")
                codebleu_original_vs_dev.append(None)
                ngram_match_original_vs_dev.append(None)
                weighted_ngram_match_original_vs_dev.append(None)
                syntax_match_original_vs_dev.append(None)
                dataflow_match_original_vs_dev.append(None)

            # Log de sucesso para os primeiros itens processados
            if index < 3:
                print(f"✅ Similaridade calculada para commit {commit_hash[:8]}: LLM vs Dev = {codebleu_llm_vs_dev[-1]:.4f}")
            elif index == 3:
                print("✅ Processamento em andamento...")
            
    except Exception as e:
        print(f"❌ Erro inesperado no processamento para o commit {commit_hash}: {e}")
        # LLM vs Dev
        codebleu_llm_vs_dev.append(None)
        ngram_match_llm_vs_dev.append(None)
        weighted_ngram_match_llm_vs_dev.append(None)
        syntax_match_llm_vs_dev.append(None)
        dataflow_match_llm_vs_dev.append(None)
        # Original vs LLM
        codebleu_original_vs_llm.append(None)
        ngram_match_original_vs_llm.append(None)
        weighted_ngram_match_original_vs_llm.append(None)
        syntax_match_original_vs_llm.append(None)
        dataflow_match_original_vs_llm.append(None)
        # Original vs Dev
        codebleu_original_vs_dev.append(None)
        ngram_match_original_vs_dev.append(None)
        weighted_ngram_match_original_vs_dev.append(None)
        syntax_match_original_vs_dev.append(None)
        dataflow_match_original_vs_dev.append(None)
        erros_processamento.append(commit_hash)

# 6. Adicione todas as colunas CodeBLEU ao DataFrame combinado
# LLM vs Dev
df_combined['codebleu_llm_vs_dev'] = codebleu_llm_vs_dev
df_combined['ngram_match_llm_vs_dev'] = ngram_match_llm_vs_dev
df_combined['weighted_ngram_match_llm_vs_dev'] = weighted_ngram_match_llm_vs_dev
df_combined['syntax_match_llm_vs_dev'] = syntax_match_llm_vs_dev
df_combined['dataflow_match_llm_vs_dev'] = dataflow_match_llm_vs_dev

# Original vs LLM
df_combined['codebleu_original_vs_llm'] = codebleu_original_vs_llm
df_combined['ngram_match_original_vs_llm'] = ngram_match_original_vs_llm
df_combined['weighted_ngram_match_original_vs_llm'] = weighted_ngram_match_original_vs_llm
df_combined['syntax_match_original_vs_llm'] = syntax_match_original_vs_llm
df_combined['dataflow_match_original_vs_llm'] = dataflow_match_original_vs_llm

# Original vs Dev
df_combined['codebleu_original_vs_dev'] = codebleu_original_vs_dev
df_combined['ngram_match_original_vs_dev'] = ngram_match_original_vs_dev
df_combined['weighted_ngram_match_original_vs_dev'] = weighted_ngram_match_original_vs_dev
df_combined['syntax_match_original_vs_dev'] = syntax_match_original_vs_dev
df_combined['dataflow_match_original_vs_dev'] = dataflow_match_original_vs_dev

# 6.1. Reorganize as colunas na ordem solicitada
df_combined = df_combined.reset_index()
df_combined = df_combined.rename(columns={'index': 'identificador'})

# Definir a ordem das colunas (todas as métricas CodeBLEU)
colunas_ordenadas = [
    'identificador',
    'codigo_original', 
    'codigo_desenvolvedor',
    'codigo_llm',
    # Original vs Dev - todas as métricas
    'codebleu_original_vs_dev',
    'ngram_match_original_vs_dev',
    'weighted_ngram_match_original_vs_dev',
    'syntax_match_original_vs_dev',
    'dataflow_match_original_vs_dev',
    # Original vs LLM - todas as métricas
    'codebleu_original_vs_llm',
    'ngram_match_original_vs_llm',
    'weighted_ngram_match_original_vs_llm',
    'syntax_match_original_vs_llm',
    'dataflow_match_original_vs_llm',
    # LLM vs Dev - todas as métricas
    'codebleu_llm_vs_dev',
    'ngram_match_llm_vs_dev',
    'weighted_ngram_match_llm_vs_dev',
    'syntax_match_llm_vs_dev',
    'dataflow_match_llm_vs_dev'
]

# Reorganizar o DataFrame com as colunas na ordem especificada
df_final = df_combined[colunas_ordenadas]

# 7. Salve o DataFrame final em um novo CSV
try:
    df_final.to_csv(CAMINHO_RESULTADO, index=False)
    print(f"\n✅ Análise completa de métricas CodeBLEU concluída! Resultados salvos em: {CAMINHO_RESULTADO}")
    print("\n📊 Todas as métricas CodeBLEU calculadas:")
    print("   • codebleu: Score principal do CodeBLEU (0-1)")
    print("   • ngram_match_score: Score de correspondência de n-gramas")
    print("   • weighted_ngram_match_score: Score ponderado de n-gramas")
    print("   • syntax_match_score: Score de correspondência sintática")
    print("   • dataflow_match_score: Score de correspondência de fluxo de dados")
    print("\n   Para cada comparação:")
    print("   • original_vs_dev: Código original vs migrado pelo desenvolvedor")
    print("   • original_vs_llm: Código original vs migrado pela LLM")
    print("   • llm_vs_dev: Código migrado pela LLM vs pelo desenvolvedor")
    
    # Estatísticas básicas
    valid_rows = df_final.dropna()
    if len(valid_rows) > 0:
        print(f"\n📈 Estatísticas das métricas principais ({len(valid_rows)} entradas válidas):")
        print("   === CODEBLEU (maior = mais similar, escala 0-1) ===")
        print(f"   • Média Original vs Dev: {valid_rows['codebleu_original_vs_dev'].mean():.4f}")
        print(f"   • Média Original vs LLM: {valid_rows['codebleu_original_vs_llm'].mean():.4f}")
        print(f"   • Média LLM vs Dev: {valid_rows['codebleu_llm_vs_dev'].mean():.4f}")
        
        print("\n   === N-GRAM MATCH SCORE ===")
        print(f"   • Média Original vs Dev: {valid_rows['ngram_match_original_vs_dev'].mean():.4f}")
        print(f"   • Média Original vs LLM: {valid_rows['ngram_match_original_vs_llm'].mean():.4f}")
        print(f"   • Média LLM vs Dev: {valid_rows['ngram_match_llm_vs_dev'].mean():.4f}")
        
        print("\n   === SYNTAX MATCH SCORE ===")
        print(f"   • Média Original vs Dev: {valid_rows['syntax_match_original_vs_dev'].mean():.4f}")
        print(f"   • Média Original vs LLM: {valid_rows['syntax_match_original_vs_llm'].mean():.4f}")
        print(f"   • Média LLM vs Dev: {valid_rows['syntax_match_llm_vs_dev'].mean():.4f}")
        
        print("\n   === DATAFLOW MATCH SCORE ===")
        print(f"   • Média Original vs Dev: {valid_rows['dataflow_match_original_vs_dev'].mean():.4f}")
        print(f"   • Média Original vs LLM: {valid_rows['dataflow_match_original_vs_llm'].mean():.4f}")
        print(f"   • Média LLM vs Dev: {valid_rows['dataflow_match_llm_vs_dev'].mean():.4f}")
    
    if erros_processamento:
        print(f"\n⚠️ Houve erros ao processar os seguintes commits: {list(set(erros_processamento))}")
except Exception as e:
    print(f"❌ Erro ao salvar o arquivo de resultados: {e}")