import pandas as pd
import json

def analisar_planilha_bugs():
    try:
        # Carregar a planilha
        df_bugs = pd.read_excel('bugs.xlsx')
        
        print("=== ANÁLISE DA PLANILHA BUGS.XLSX ===")
        print(f"\nTotal de registros: {len(df_bugs)}")
        print(f"Total de colunas: {len(df_bugs.columns)}")
        
        print("\n=== COLUNAS ENCONTRADAS ===")
        for i, col in enumerate(df_bugs.columns, 1):
            print(f"{i}. {col}")
        
        print("\n=== TIPOS DE DADOS ===")
        for col, tipo in df_bugs.dtypes.items():
            print(f"{col}: {tipo}")
        
        print("\n=== VALORES NULOS POR COLUNA ===")
        nulos = df_bugs.isnull().sum()
        for col, qtd_nulos in nulos.items():
            perc_nulos = (qtd_nulos / len(df_bugs)) * 100
            print(f"{col}: {qtd_nulos} ({perc_nulos:.1f}%)")
        
        print("\n=== PRIMEIRAS 5 LINHAS ===")
        print(df_bugs.head().to_string())
        
        print("\n=== VALORES ÚNICOS EM COLUNAS CATEGÓRICAS ===")
        for col in df_bugs.columns:
            if df_bugs[col].dtype == 'object' and df_bugs[col].nunique() < 20:
                valores_unicos = df_bugs[col].value_counts()
                print(f"\n{col}:")
                for valor, qtd in valores_unicos.items():
                    print(f"  {valor}: {qtd}")
        
        # Salvar análise em arquivo JSON
        analise = {
            'total_registros': len(df_bugs),
            'total_colunas': len(df_bugs.columns),
            'colunas': list(df_bugs.columns),
            'tipos_dados': {col: str(tipo) for col, tipo in df_bugs.dtypes.items()},
            'valores_nulos': {col: int(qtd) for col, qtd in df_bugs.isnull().sum().items()},
            'amostra_dados': df_bugs.head().to_dict('records')
        }
        
        with open('analise_bugs.json', 'w', encoding='utf-8') as f:
            json.dump(analise, f, indent=2, ensure_ascii=False, default=str)
        
        print("\n=== ANÁLISE SALVA EM 'analise_bugs.json' ===")
        
        return df_bugs, analise
        
    except Exception as e:
        print(f"Erro ao analisar planilha: {e}")
        return None, None

if __name__ == "__main__":
    df_bugs, analise = analisar_planilha_bugs()