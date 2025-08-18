import pandas as pd
import streamlit as st
from google_sheets_integration import load_google_sheets_data_automatically

def debug_resultado_testes():
    print("=== DEBUG: Resultado dos Testes de Qualidade ===")
    
    try:
        df = load_google_sheets_data_automatically()
        if df is None or df.empty:
            print("❌ Erro: DataFrame vazio ou None")
            return
        
        print(f"📊 Total de registros carregados: {len(df)}")
        print(f"📋 Colunas disponíveis: {list(df.columns)}")
        
        # Verificar se existe coluna Status
        if 'Status' not in df.columns:
            print("❌ Coluna 'Status' não encontrada!")
            return
        
        # Filtrar apenas dados com teste (como no dashboard)
        if 'Responsavel pelo teste' in df.columns:
            df_com_teste = df[df['Responsavel pelo teste'].notna()]
        else:
            df_com_teste = df[df['Status'].notna()]
        
        print(f"🧪 Registros com teste: {len(df_com_teste)}")
        
        # Analisar valores únicos na coluna Status
        print("\n=== ANÁLISE DA COLUNA STATUS ===")
        status_counts = df_com_teste['Status'].value_counts()
        print("📈 Contagem por Status:")
        for status, count in status_counts.items():
            print(f"  - '{status}': {count}")
        
        # Verificar se existe algum status com valor "2"
        print(f"\n🔍 Valores únicos na coluna Status: {df_com_teste['Status'].unique()}")
        
        # Verificar registros específicos
        print("\n=== REGISTROS DETALHADOS ===")
        for idx, row in df_com_teste.head(10).iterrows():
            status = row.get('Status', 'N/A')
            responsavel = row.get('Responsavel pelo teste', 'N/A')
            task = row.get('Nome da Task', 'N/A')
            print(f"Linha {idx}: Status='{status}' | Responsável='{responsavel}' | Task='{task[:50]}...'")
        
        # Verificar se há algum problema com tipos de dados
        print(f"\n📊 Tipo da coluna Status: {df_com_teste['Status'].dtype}")
        print(f"🔢 Valores nulos na coluna Status: {df_com_teste['Status'].isnull().sum()}")
        
        # Verificar se há valores numéricos sendo interpretados como string
        status_values = df_com_teste['Status'].astype(str).unique()
        print(f"🔤 Status como string: {status_values}")
        
        # Verificar se algum status contém apenas números
        numeric_status = [s for s in status_values if s.isdigit()]
        if numeric_status:
            print(f"⚠️ Status numéricos encontrados: {numeric_status}")
            
            # Mostrar registros com status numérico
            for num_status in numeric_status:
                registros = df_com_teste[df_com_teste['Status'].astype(str) == num_status]
                print(f"\n📋 Registros com Status '{num_status}':")
                for idx, row in registros.iterrows():
                    print(f"  - Linha {idx}: {row.get('Nome da Task', 'N/A')[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro durante debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_resultado_testes()