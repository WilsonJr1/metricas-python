import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_sheets_integration import load_google_sheets_data_automatically
import pandas as pd

print("=== DEBUG DETALHADO - PRINCIPAL TIPO DE DEFEITO ===")
print()

secrets_path = r"C:\Users\JoséWilsondoSantosJu\OneDrive - Delbank\Documentos\Metrica\metricas-python\secrets"
os.environ['SECRETS_PATH'] = secrets_path

try:
    df = load_google_sheets_data_automatically()
    print(f"✅ Dados carregados: {len(df)} registros")
    print(f"Colunas disponíveis: {list(df.columns)}")
    print()
    
    if 'Status' in df.columns:
        df_rejeitadas = df[df['Status'] == 'REJEITADA']
        print(f"📊 Tarefas rejeitadas: {len(df_rejeitadas)}")
        
        if not df_rejeitadas.empty:
            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
            motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
            print(f"Colunas de motivos encontradas: {motivos_existentes}")
            
            if motivos_existentes:
                todos_motivos = []
                for col in motivos_existentes:
                    motivos = df_rejeitadas[col].dropna().tolist()
                    todos_motivos.extend(motivos)
                
                print(f"Total de motivos coletados: {len(todos_motivos)}")
                print(f"Primeiros 10 motivos: {todos_motivos[:10]}")
                print()
                
                if todos_motivos:
                    motivos_filtrados = [motivo for motivo in todos_motivos 
                                       if motivo.lower() not in ['aprovada', 'sem recusa']]
                    
                    print(f"Motivos após filtrar 'aprovada' e 'sem recusa': {len(motivos_filtrados)}")
                    print()
                    
                    if motivos_filtrados:
                        contagem_motivos = pd.Series(motivos_filtrados).value_counts()
                        print("=== TOP 10 MOTIVOS MAIS COMUNS ===")
                        for i, (motivo, count) in enumerate(contagem_motivos.head(10).items()):
                            print(f"{i+1}. '{motivo}' - {count} ocorrências (tamanho: {len(motivo)} caracteres)")
                        print()
                        
                        motivo_mais_comum = contagem_motivos.index[0]
                        ocorrencias = contagem_motivos.iloc[0]
                        
                        print(f"🎯 PRINCIPAL DEFEITO IDENTIFICADO:")
                        print(f"   Motivo: '{motivo_mais_comum}'")
                        print(f"   Ocorrências: {ocorrencias}")
                        print(f"   Tamanho do texto: {len(motivo_mais_comum)} caracteres")
                        print()
                        
                        print("=== VERIFICAÇÕES ADICIONAIS ===")
                        print(f"Motivo contém caracteres especiais: {any(not c.isalnum() and c != ' ' for c in motivo_mais_comum)}")
                        print(f"Motivo é maior que 15 caracteres: {len(motivo_mais_comum) > 15}")
                        print(f"Motivo em minúsculas: '{motivo_mais_comum.lower()}'")
                        print(f"Motivo sem espaços: '{motivo_mais_comum.strip()}'")
                        
                        print("\n=== ANÁLISE DE TODOS OS MOTIVOS POR TAMANHO ===")
                        motivos_por_tamanho = {}
                        for motivo in set(motivos_filtrados):
                            tamanho = len(motivo)
                            if tamanho not in motivos_por_tamanho:
                                motivos_por_tamanho[tamanho] = []
                            motivos_por_tamanho[tamanho].append(motivo)
                        
                        for tamanho in sorted(motivos_por_tamanho.keys()):
                            print(f"Tamanho {tamanho}: {len(motivos_por_tamanho[tamanho])} motivos únicos")
                            if tamanho > 15:
                                print(f"  Motivos > 15 chars: {motivos_por_tamanho[tamanho][:3]}...")
                    else:
                        print("❌ Nenhum motivo válido após filtragem")
                else:
                    print("❌ Lista de motivos está vazia")
            else:
                print("❌ Colunas de motivos não encontradas")
        else:
            print("❌ Nenhuma tarefa rejeitada encontrada")
    else:
        print("❌ Coluna 'Status' não encontrada")
        
except Exception as e:
    print(f"❌ Erro ao carregar dados: {e}")
    import traceback
    traceback.print_exc()