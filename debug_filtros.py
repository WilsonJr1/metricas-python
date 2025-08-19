import pandas as pd
from google_sheets_integration import load_google_sheets_data_automatically
import streamlit as st
import os

print("=== DEBUG: Verificação de Filtros ===")

# Configurar secrets para teste local
os.environ['STREAMLIT_SECRETS_PATH'] = 'secrets.toml'

try:
    df = load_google_sheets_data_automatically()
    print(f"Total de registros carregados: {len(df)}")
    
    # Processar dados como no dashboard
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    
    if 'Status' in df.columns:
        df['Status'] = df['Status'].replace('PRONTO PARA PUBLICAÇÃO', 'APROVADA')
    
    print("\n=== Dados Originais ===")
    print(f"Total de registros: {len(df)}")
    print(f"Status únicos: {df['Status'].value_counts().to_dict()}")
    
    # Simular filtros que podem estar ativos
    print("\n=== Simulando Filtros Possíveis ===")
    
    # 1. Filtro por responsável pelo teste (Eduardo e Wilson)
    if 'Responsavel pelo teste' in df.columns:
        df_filtrado_responsavel = df[df['Responsavel pelo teste'].isin(['Eduardo', 'Wilson'])]
        print(f"\nApós filtrar responsáveis (Eduardo, Wilson): {len(df_filtrado_responsavel)} registros")
        if len(df_filtrado_responsavel) > 0:
            df_rejeitadas_resp = df_filtrado_responsavel[df_filtrado_responsavel['Status'] == 'REJEITADA']
            print(f"Tarefas rejeitadas após filtro responsável: {len(df_rejeitadas_resp)}")
    
    # 2. Filtro por motivo SEM TESTE
    if 'Motivo' in df.columns:
        sem_teste_mask = df['Motivo'].str.upper().str.contains('SEM TESTE', na=False)
        df_com_teste = df[~sem_teste_mask]
        print(f"\nApós remover 'SEM TESTE': {len(df_com_teste)} registros")
        
        # Aplicar filtro de responsável nos dados COM teste
        if 'Responsavel pelo teste' in df_com_teste.columns:
            df_com_teste_filtrado = df_com_teste[df_com_teste['Responsavel pelo teste'].isin(['Eduardo', 'Wilson'])]
            print(f"Com teste + responsáveis filtrados: {len(df_com_teste_filtrado)} registros")
            
            df_rejeitadas_final = df_com_teste_filtrado[df_com_teste_filtrado['Status'] == 'REJEITADA']
            print(f"Tarefas rejeitadas finais: {len(df_rejeitadas_final)}")
            
            if not df_rejeitadas_final.empty:
                print("\n=== Calculando Principal Defeito com Filtros ===")
                motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
                todos_motivos = []
                
                for col in motivos_cols:
                    if col in df_rejeitadas_final.columns:
                        motivos = df_rejeitadas_final[col].dropna().tolist()
                        todos_motivos.extend(motivos)
                
                if todos_motivos:
                    motivos_filtrados = [motivo for motivo in todos_motivos 
                                       if str(motivo).lower() not in ['aprovada', 'sem recusa', 'nan', '']]
                    
                    if motivos_filtrados:
                        contagem_motivos = pd.Series(motivos_filtrados).value_counts()
                        print(f"\nTOP 5 DEFEITOS COM FILTROS:")
                        print(contagem_motivos.head(5))
                        
                        motivo_mais_comum = contagem_motivos.index[0]
                        ocorrencias = contagem_motivos.iloc[0]
                        print(f"\n🔍 PRINCIPAL DEFEITO COM FILTROS: {motivo_mais_comum} ({ocorrencias}x)")
                    else:
                        print("\n❌ Nenhum motivo válido após filtros")
                else:
                    print("\n❌ Nenhum motivo encontrado após filtros")
            else:
                print("\n❌ Nenhuma tarefa rejeitada após aplicar todos os filtros")
    
    # 3. Verificar se há filtros de data, sprint, time, etc. que podem estar ativos
    print("\n=== Verificação de Outros Filtros Possíveis ===")
    
    if 'Sprint' in df.columns:
        sprints_disponiveis = df['Sprint'].dropna().unique()
        print(f"Sprints disponíveis: {len(sprints_disponiveis)} ({list(sprints_disponiveis)[:5]}...)")
    
    if 'Time' in df.columns:
        times_disponiveis = df['Time'].dropna().unique()
        print(f"Times disponíveis: {len(times_disponiveis)} ({list(times_disponiveis)})")
    
    if 'Responsável' in df.columns:
        devs_disponiveis = df['Responsável'].dropna().unique()
        print(f"Desenvolvedores disponíveis: {len(devs_disponiveis)} ({list(devs_disponiveis)[:5]}...)")
    
    if 'Data' in df.columns:
        data_min = df['Data'].min()
        data_max = df['Data'].max()
        print(f"Período de dados: {data_min} a {data_max}")
        
except Exception as e:
    print(f"\n❌ Erro ao processar dados: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== FIM DO DEBUG ===")