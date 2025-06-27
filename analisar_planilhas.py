import pandas as pd
import os

def analisar_planilhas():
    """
    Script para analisar as planilhas do módulo de sustentação
    """
    
    # Caminhos das planilhas
    planilha1 = r"c:\Users\JoséWilsondoSantosJu\OneDrive - Delbank\Documentos\Metrica\metricas-python\Planilha sem título.xlsx"
    planilha2 = r"c:\Users\JoséWilsondoSantosJu\OneDrive - Delbank\Documentos\Metrica\metricas-python\Planilha horas por dev.xlsx"
    
    print("=== ANÁLISE DAS PLANILHAS DE SUSTENTAÇÃO ===")
    print()
    
    # Verificar se os arquivos existem
    for i, arquivo in enumerate([planilha1, planilha2], 1):
        print(f"Planilha {i}: {os.path.basename(arquivo)}")
        if os.path.exists(arquivo):
            print(f"✓ Arquivo encontrado")
            
            try:
                # Tentar ler a planilha
                df = pd.read_excel(arquivo)
                print(f"✓ Planilha lida com sucesso")
                print(f"  - Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
                print(f"  - Colunas: {list(df.columns)}")
                print(f"  - Primeiras 5 linhas:")
                print(df.head())
                print(f"  - Tipos de dados:")
                print(df.dtypes)
                print(f"  - Valores únicos por coluna:")
                for col in df.columns:
                    unique_count = df[col].nunique()
                    print(f"    {col}: {unique_count} valores únicos")
                    if unique_count <= 10:
                        print(f"      Valores: {df[col].unique().tolist()}")
                
            except Exception as e:
                print(f"✗ Erro ao ler planilha: {e}")
                
                # Tentar ler diferentes abas
                try:
                    xl_file = pd.ExcelFile(arquivo)
                    print(f"  - Abas disponíveis: {xl_file.sheet_names}")
                    
                    for sheet in xl_file.sheet_names:
                        try:
                            df_sheet = pd.read_excel(arquivo, sheet_name=sheet)
                            print(f"  - Aba '{sheet}': {df_sheet.shape[0]} linhas x {df_sheet.shape[1]} colunas")
                            print(f"    Colunas: {list(df_sheet.columns)}")
                        except Exception as sheet_error:
                            print(f"    Erro na aba '{sheet}': {sheet_error}")
                            
                except Exception as xl_error:
                    print(f"  - Erro ao analisar abas: {xl_error}")
        else:
            print(f"✗ Arquivo não encontrado")
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    analisar_planilhas()