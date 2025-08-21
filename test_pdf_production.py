#!/usr/bin/env python3
"""
Script de teste para verificar a geração de PDFs em produção
Especialmente projetado para diagnosticar problemas no Streamlit Cloud
"""

import os
import sys
import traceback
from datetime import datetime

def test_imports():
    """Testa se todas as dependências estão disponíveis"""
    print("=== TESTE DE IMPORTAÇÕES ===")
    
    dependencies = {
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'kaleido': 'kaleido', 
        'reportlab': 'reportlab',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    results = {}
    
    for name, module in dependencies.items():
        try:
            __import__(module)
            if name == 'kaleido':
                import kaleido
                version = kaleido.__version__
            elif name == 'plotly':
                import plotly
                version = plotly.__version__
            else:
                version = "OK"
            
            results[name] = f"✅ {version}"
            print(f"{name}: ✅ {version}")
        except ImportError as e:
            results[name] = f"❌ {str(e)}"
            print(f"{name}: ❌ {str(e)}")
    
    return results

def test_environment():
    """Testa o ambiente de execução"""
    print("\n=== TESTE DE AMBIENTE ===")
    
    env_vars = [
        'STREAMLIT_SHARING_MODE',
        'STREAMLIT_CLOUD', 
        'HOSTNAME',
        'USER',
        'PWD',
        'DISPLAY',
        'KALEIDO_USE_SWIFT',
        'PLOTLY_RENDERER'
    ]
    
    print(f"Diretório atual: {os.getcwd()}")
    print(f"Python: {sys.version}")
    print(f"Plataforma: {sys.platform}")
    
    for var in env_vars:
        value = os.getenv(var, 'NÃO DEFINIDO')
        print(f"{var}: {value}")
    
    # Detectar Streamlit Cloud
    indicators = [
        os.getenv('STREAMLIT_SHARING_MODE') == 'true',
        'streamlit.io' in os.getenv('HOSTNAME', ''),
        os.getenv('STREAMLIT_CLOUD') == 'true',
        'streamlit' in os.getenv('USER', '').lower(),
        '/mount/src' in os.getcwd(),
        'streamlit-cloud' in os.getenv('HOSTNAME', '').lower()
    ]
    
    is_cloud = any(indicators)
    print(f"\n🔍 Streamlit Cloud detectado: {is_cloud} ({sum(indicators)}/6 indicadores)")
    
    return is_cloud

def test_kaleido_basic():
    """Teste básico do Kaleido"""
    print("\n=== TESTE BÁSICO DO KALEIDO ===")
    
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        import kaleido
        
        print(f"Kaleido versão: {kaleido.__version__}")
        print(f"Plotly versão: {go.__version__ if hasattr(go, '__version__') else 'N/A'}")
        
        # Configurações atuais
        if hasattr(pio, 'kaleido'):
            print(f"Timeout atual: {pio.kaleido.scope.default_timeout}")
            print(f"Argumentos Chromium: {len(pio.kaleido.scope.chromium_args)} argumentos")
            print(f"Primeiros 5 args: {list(pio.kaleido.scope.chromium_args)[:5]}")
        
        # Criar gráfico simples
        fig = go.Figure(data=go.Bar(x=['A', 'B', 'C'], y=[1, 2, 3]))
        fig.update_layout(
            title="Teste Kaleido - Produção",
            width=400,
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        print("Tentando converter gráfico para PNG...")
        
        # Teste de conversão
        img_bytes = fig.to_image(format="png", width=400, height=300)
        
        if img_bytes and len(img_bytes) > 100:
            print(f"✅ Sucesso! Imagem gerada: {len(img_bytes)} bytes")
            return True
        else:
            print(f"❌ Falha! Imagem muito pequena: {len(img_bytes) if img_bytes else 0} bytes")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do Kaleido: {e}")
        traceback.print_exc()
        return False

def test_kaleido_advanced():
    """Teste avançado com múltiplas estratégias"""
    print("\n=== TESTE AVANÇADO DO KALEIDO ===")
    
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        
        # Aplicar configurações de produção
        try:
            from streamlit_config import configure_plotly_for_streamlit
            configure_plotly_for_streamlit()
            print("✅ Configurações de produção aplicadas")
        except Exception as e:
            print(f"⚠️ Erro ao aplicar configurações: {e}")
        
        # Criar gráfico mais complexo
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13], name='Série 1'))
        fig.add_trace(go.Scatter(x=[1, 2, 3, 4], y=[16, 15, 14, 13], name='Série 2'))
        
        fig.update_layout(
            title="Teste Avançado - Múltiplas Séries",
            width=600,
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True
        )
        
        # Testar múltiplas estratégias
        strategies = [
            {"format": "png", "width": 600, "height": 400},
            {"format": "png", "width": 400, "height": 300},
            {"format": "jpeg", "width": 400, "height": 300},
            {"format": "png", "width": 300, "height": 200}
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                print(f"Estratégia {i+1}: {strategy['format']} {strategy['width']}x{strategy['height']}")
                
                img_bytes = fig.to_image(
                    format=strategy['format'],
                    width=strategy['width'],
                    height=strategy['height']
                )
                
                if img_bytes and len(img_bytes) > 100:
                    print(f"  ✅ Sucesso: {len(img_bytes)} bytes")
                    return True
                else:
                    print(f"  ❌ Falha: {len(img_bytes) if img_bytes else 0} bytes")
                    
            except Exception as e:
                print(f"  ❌ Erro: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro no teste avançado: {e}")
        traceback.print_exc()
        return False

def test_pdf_generation():
    """Teste de geração de PDF completo"""
    print("\n=== TESTE DE GERAÇÃO DE PDF ===")
    
    try:
        from dashboard import exportar_grafico_para_pdf
        import plotly.graph_objects as go
        import pandas as pd
        
        # Criar dados de teste
        df_test = pd.DataFrame({
            'Status': ['APROVADA', 'REJEITADA', 'APROVADA', 'REJEITADA'],
            'Time': ['Time A', 'Time B', 'Time A', 'Time C'],
            'Responsavel': ['Dev1', 'Dev2', 'Dev3', 'Dev4']
        })
        
        # Criar gráfico de teste
        fig = go.Figure(data=go.Bar(
            x=df_test['Status'].value_counts().index,
            y=df_test['Status'].value_counts().values
        ))
        
        fig.update_layout(
            title="Teste PDF - Status Distribution",
            width=600,
            height=400
        )
        
        print("Testando função exportar_grafico_para_pdf...")
        
        # Testar função de exportação
        img_bytes = exportar_grafico_para_pdf(fig, "Teste PDF")
        
        if img_bytes and len(img_bytes) > 100:
            print(f"✅ PDF Export Sucesso: {len(img_bytes)} bytes")
            return True
        else:
            print(f"❌ PDF Export Falha: {len(img_bytes) if img_bytes else 0} bytes")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de PDF: {e}")
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    print(f"🚀 INICIANDO TESTES DE PRODUÇÃO - {datetime.now()}")
    print("=" * 60)
    
    results = {
        'imports': test_imports(),
        'environment': test_environment(),
        'kaleido_basic': test_kaleido_basic(),
        'kaleido_advanced': test_kaleido_advanced(),
        'pdf_generation': test_pdf_generation()
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results.items():
        if isinstance(result, dict):
            print(f"{test_name.upper()}:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name.upper()}: {status}")
    
    print("\n" + "=" * 60)
    print(f"🏁 TESTES CONCLUÍDOS - {datetime.now()}")
    
    return results

if __name__ == "__main__":
    main()