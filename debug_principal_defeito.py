import pandas as pd
from google_sheets_integration import load_google_sheets_data_automatically
import streamlit as st
import os

print("=== DEBUG: Principal Tipo de Defeito ===")

# Configurar secrets para teste local
os.environ['STREAMLIT_SECRETS_PATH'] = 'secrets.toml'

try:
    df = load_google_sheets_data_automatically()
    print(f"Total de registros carregados: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")
    
    print("\n=== Status únicos ===")
    print(df['Status'].value_counts())
    
    df_rejeitadas = df[df['Status'] == 'REJEITADA'].copy()
    print(f"\nTotal de tarefas rejeitadas: {len(df_rejeitadas)}")
    
    if not df_rejeitadas.empty:
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
        motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
        print(f"\nColunas de motivos encontradas: {motivos_existentes}")
        
        if motivos_existentes:
            todos_motivos = []
            for col in motivos_existentes:
                motivos = df_rejeitadas[col].dropna().tolist()
                print(f"\nMotivos em {col}: {len(motivos)} valores")
                if motivos:
                    print(f"Primeiros 5 valores: {motivos[:5]}")
                todos_motivos.extend(motivos)
            
            print(f"\nTotal de motivos coletados: {len(todos_motivos)}")
            
            if todos_motivos:
                motivos_filtrados = [motivo for motivo in todos_motivos 
                                   if str(motivo).lower() not in ['aprovada', 'sem recusa', 'nan', '']]
                
                print(f"Motivos após filtrar 'aprovada' e 'sem recusa': {len(motivos_filtrados)}")
                
                if motivos_filtrados:
                    contagem_motivos = pd.Series(motivos_filtrados).value_counts()
                    print("\n=== TOP 10 PRINCIPAIS DEFEITOS ===")
                    print(contagem_motivos.head(10))
                    
                    motivo_mais_comum = contagem_motivos.index[0]
                    ocorrencias = contagem_motivos.iloc[0]
                    
                    print(f"\n🔍 PRINCIPAL TIPO DE DEFEITO: {motivo_mais_comum}")
                    print(f"📊 OCORRÊNCIAS: {ocorrencias}x")
                    
                else:
                    print("\n❌ Nenhum motivo válido encontrado após filtros")
            else:
                print("\n❌ Nenhum motivo encontrado nas colunas")
        else:
            print("\n❌ Colunas de motivos não encontradas")
    else:
        print("\n❌ Nenhuma tarefa rejeitada encontrada")
        
except Exception as e:
    print(f"\n❌ Erro ao processar dados: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== FIM DO DEBUG ===")