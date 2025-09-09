import pandas as pd
import os
from codebleu import calc_codebleu

def calcular_codebleu(reference_code, prediction_code, lang="javascript"):
    """
    Calcula o CodeBLEU de forma robusta, garantindo que os inputs sejam válidos.
    Retorna o score ou None em caso de erro ou código inválido.
    """
    # 1. Converte e limpa as strings
    reference_str = str(reference_code).strip()
    prediction_str = str(prediction_code).strip()
    
    # 2. Verifica se as strings não estão vazias após a limpeza
    if not reference_str or not prediction_str:
        print("⚠️ Aviso: Uma das strings de código está vazia. Retornando None.")
        return None
        
    try:
        # 3. Define os pesos CodeBLEU explicitamente
        pesos_codebleu = (0.25, 0.25, 0.25, 0.25)
        
        # 4. Chama a função de cálculo
        resultado = calc_codebleu(
            references=[reference_str],
            predictions=[prediction_str],
            lang=lang,
            weights=pesos_codebleu
        )
        return resultado.get('codebleu', None)
        
    except Exception as e:
        print(f"❌ Erro ao calcular CodeBLEU: {e}")
        return None

# --- Dados para teste ---
# CÓDIGO DE REFERÊNCIA (o código "correto" ou o do desenvolvedor)
codigo_de_referencia = """
function calcularPrecoFinal(preco, desconto) {
  let precoFinal = preco * (1 - desconto);
  return precoFinal;
}

const resultado = calcularPrecoFinal(100, 0.1);
console.log(resultado);
"""

# CÓDIGO DE PREVISÃO (o código gerado pela LLM)
codigo_de_previsao = """
const calcularPrecoComDesconto = (valor, percentualDesconto) => {
  const valorFinal = valor * (1 - percentualDesconto);
  return valorFinal;
};

const precoComDesconto = calcularPrecoComDesconto(100, 0.1);
console.log(precoComDesconto);
"""

# Teste 1: Casos Válidos
print("--- Testando com códigos válidos ---")
score_valido = calcular_codebleu(codigo_de_referencia, codigo_de_previsao)
if score_valido is not None:
    print(f"Score CodeBLEU para casos válidos: {score_valido:.4f}\n")
else:
    print("O cálculo do CodeBLEU para casos válidos falhou.\n")