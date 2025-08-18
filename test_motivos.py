import pandas as pd
from google_sheets_integration import load_google_sheets_data_automatically

df = load_google_sheets_data_automatically()
if df is not None:
    df_rejeitadas = df[df['Status'] == 'REJEITADA']
    print(f'Total rejeitadas: {len(df_rejeitadas)}')
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
    todos_motivos = []
    
    for col in motivos_cols:
        if col in df_rejeitadas.columns:
            motivos = df_rejeitadas[col].dropna().tolist()
            todos_motivos.extend(motivos)
    
    print(f'Total motivos encontrados: {len(todos_motivos)}')
    
    motivos_filtrados = [motivo for motivo in todos_motivos 
                        if motivo.lower() not in ['aprovada', 'sem recusa', '']]
    
    print(f'Motivos válidos: {len(motivos_filtrados)}')
    
    if motivos_filtrados:
        motivo_mais_comum = pd.Series(motivos_filtrados).value_counts()
        print('\nTop 5 motivos mais comuns:')
        print(motivo_mais_comum.head())
        print(f'\nMotivo mais comum: {motivo_mais_comum.index[0]} com {motivo_mais_comum.iloc[0]} ocorrências')
    else:
        print('Nenhum motivo válido encontrado')
else:
    print('Não foi possível carregar os dados')