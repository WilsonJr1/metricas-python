#!/usr/bin/env python3
"""
Teste FINAL para verificar se os PDFs com gráficos funcionam em produção
Este script deve ser executado no Streamlit Cloud para diagnóstico
"""

import os
import sys
from datetime import datetime

def test_environment():
    """Testa o ambiente de execução"""
    print("=== TESTE DE AMBIENTE ===")
    print(f"Python: {sys.version}")
    print(f"OS: {os.name}")
    print(f"CWD: {os.getcwd()}")
    
    # Variáveis de ambiente importantes
    env_vars = ['MPLBACKEND', 'DISPLAY', 'KALEIDO_DISABLE_GPU', 'CHROMIUM_FLAGS']
    for var in env_vars:
        print(f"{var}: {os.getenv(var, 'NÃO DEFINIDA')}")

def test_imports():
    """Testa importações críticas"""
    print("\n=== TESTE DE IMPORTAÇÕES ===")
    
    modules = {
        'streamlit': 'st',
        'plotly.graph_objects': 'go', 
        'plotly.io': 'pio',
        'kaleido': 'kaleido',
        'reportlab.platypus': 'SimpleDocTemplate',
        'pandas': 'pd',
        'numpy': 'np'
    }
    
    success = 0
    for module, alias in modules.items():
        try:
            exec(f"import {module} as {alias}")
            print(f"✅ {module}")
            success += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")
    
    print(f"\nImportações: {success}/{len(modules)} OK")
    return success == len(modules)

def test_kaleido_basic():
    """Teste básico do Kaleido"""
    print("\n=== TESTE KALEIDO BÁSICO ===")
    
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        
        # Mostrar configurações atuais
        print(f"Timeout: {pio.kaleido.scope.default_timeout}")
        print(f"Chromium args: {len(pio.kaleido.scope.chromium_args)} argumentos")
        
        # Criar gráfico simples
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['A', 'B'], y=[1, 2]))
        fig.update_layout(
            title="Teste Produção",
            width=400,
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Tentar converter
        print("Tentando conversão...")
        img_bytes = fig.to_image(format="png", width=400, height=300)
        
        if img_bytes and len(img_bytes) > 100:
            print(f"✅ Kaleido OK: {len(img_bytes)} bytes gerados")
            return True
        else:
            print(f"❌ Kaleido falhou: {len(img_bytes) if img_bytes else 0} bytes")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste Kaleido: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_generation():
    """Testa geração de PDF com gráfico"""
    print("\n=== TESTE GERAÇÃO PDF ===")
    
    try:
        from dashboard import exportar_grafico_para_pdf
        import plotly.graph_objects as go
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.lib.pagesizes import A4
        import io
        
        # Criar gráfico de teste
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['Aprovadas', 'Rejeitadas', 'Em Teste'],
            y=[10, 5, 3],
            marker_color=['green', 'red', 'orange']
        ))
        fig.update_layout(
            title="Teste Dashboard PDF",
            width=600,
            height=400
        )
        
        # Tentar exportar gráfico
        print("Exportando gráfico...")
        img_obj = exportar_grafico_para_pdf(fig, "Teste Produção")
        
        if img_obj:
            print("✅ Gráfico exportado com sucesso")
            
            # Tentar criar PDF
            print("Criando PDF...")
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = [img_obj]
            doc.build(story)
            
            pdf_size = len(buffer.getvalue())
            print(f"✅ PDF criado: {pdf_size} bytes")
            
            return pdf_size > 1000
        else:
            print("❌ Falha ao exportar gráfico")
            return False
            
    except Exception as e:
        print(f"❌ Erro na geração PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    print(f"TESTE FINAL DE PRODUÇÃO - {datetime.now()}")
    print("=" * 50)
    
    # Aplicar configurações
    try:
        from config_production import setup_production_environment
        setup_production_environment()
    except:
        print("⚠️ Configurações de produção não aplicadas")
    
    # Executar testes
    test_environment()
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ FALHA: Importações básicas falharam")
        return False
    
    kaleido_ok = test_kaleido_basic()
    pdf_ok = test_pdf_generation()
    
    # Resultado final
    print("\n" + "=" * 50)
    if kaleido_ok and pdf_ok:
        print("🎉 SUCESSO: Todos os testes passaram!")
        print("✅ PDFs com gráficos devem funcionar em produção")
        return True
    else:
        print("❌ FALHA: Alguns testes falharam")
        print(f"Kaleido: {'✅' if kaleido_ok else '❌'}")
        print(f"PDF: {'✅' if pdf_ok else '❌'}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)