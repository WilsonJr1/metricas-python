#!/usr/bin/env python3

import sys
import os
import io
from datetime import datetime

print("=" * 60)
print("TESTE ULTRA-ROBUSTO DE GERAÇÃO DE PDF COM GRÁFICOS")
print("=" * 60)
print(f"Timestamp: {datetime.now()}")
print(f"Python: {sys.version}")
print(f"Plataforma: {sys.platform}")
print(f"Diretório: {os.getcwd()}")

try:
    from config_production import setup_production_environment, verify_dependencies
    print("✅ Configurações de produção importadas")
    
    setup_production_environment()
    print("✅ Ambiente de produção configurado")
    
    verify_dependencies()
    print("✅ Dependências verificadas")
    
except Exception as e:
    print(f"⚠️ Erro nas configurações: {e}")

print("\n" + "=" * 40)
print("TESTE 1: Importações Críticas")
print("=" * 40)

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    print("✅ Plotly importado")
    
    import kaleido
    print("✅ Kaleido importado (versão não disponível)")
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.units import inch
    print("✅ ReportLab importado")
    
except Exception as e:
    print(f"❌ Erro nas importações: {e}")
    print("⚠️ Continuando mesmo com erro...")
    # Não sair, continuar com os testes

print("\n" + "=" * 40)
print("TESTE 2: Configurações do Kaleido")
print("=" * 40)

try:
    print(f"Argumentos Chromium: {pio.kaleido.scope.chromium_args}")
    print(f"Timeout: {pio.kaleido.scope.default_timeout}")
    print(f"Variáveis de ambiente:")
    for var in ['MPLBACKEND', 'DISPLAY', 'KALEIDO_DISABLE_GPU', 'CHROMIUM_FLAGS']:
        print(f"  {var}: {os.environ.get(var, 'NÃO DEFINIDA')}")
except Exception as e:
    print(f"❌ Erro ao verificar configurações: {e}")

print("\n" + "=" * 40)
print("TESTE 3: Criação de Gráfico Simples")
print("=" * 40)

try:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Jan', 'Fev', 'Mar', 'Abr', 'Mai'],
        y=[10, 15, 13, 17, 20],
        name='Vendas',
        marker_color='blue'
    ))
    
    fig.update_layout(
        title='Teste de Gráfico de Barras',
        xaxis_title='Meses',
        yaxis_title='Valores',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    print("✅ Gráfico criado com sucesso")
    print(f"Dados do gráfico: {len(fig.data)} traces")
    
except Exception as e:
    print(f"❌ Erro ao criar gráfico: {e}")
    sys.exit(1)

print("\n" + "=" * 40)
print("TESTE 4: Função Ultra-Robusta")
print("=" * 40)

try:
    from dashboard import exportar_grafico_para_pdf
    print("✅ Função importada")
    
    print("\n🔄 Testando conversão ultra-robusta...")
    resultado = exportar_grafico_para_pdf(fig, "Teste Ultra-Robusto")
    
    if resultado:
        print(f"✅ SUCESSO! Resultado: {type(resultado)}")
        if hasattr(resultado, 'width') and hasattr(resultado, 'height'):
            print(f"Dimensões: {resultado.width} x {resultado.height}")
    else:
        print("❌ FALHA! Resultado é None")
        
except Exception as e:
    print(f"❌ Erro na função ultra-robusta: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 40)
print("TESTE 5: Geração de PDF Completo")
print("=" * 40)

try:
    pdf_filename = f"teste_ultra_robusto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("TESTE ULTRA-ROBUSTO DE PDF", styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Gerado em: {datetime.now()}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    resultado_img = exportar_grafico_para_pdf(fig, "Gráfico de Teste Final")
    
    if resultado_img:
        story.append(Paragraph("Gráfico gerado com SUCESSO:", styles['Heading2']))
        story.append(Spacer(1, 10))
        story.append(resultado_img)
        print("✅ Gráfico adicionado ao PDF")
    else:
        story.append(Paragraph("❌ FALHA na geração do gráfico", styles['Heading2']))
        print("❌ Gráfico NÃO foi adicionado ao PDF")
    
    doc.build(story)
    
    if os.path.exists(pdf_filename):
        file_size = os.path.getsize(pdf_filename)
        print(f"✅ PDF criado: {pdf_filename} ({file_size} bytes)")
    else:
        print("❌ PDF não foi criado")
        
except Exception as e:
    print(f"❌ Erro na geração do PDF: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TESTE ULTRA-ROBUSTO CONCLUÍDO")
print("=" * 60)
print("\nSe você vê gráficos nos PDFs localmente mas não em produção,")
print("execute este script no Streamlit Cloud para diagnosticar o problema.")
print("\nComandos para debug no Streamlit Cloud:")
print("1. Adicione este arquivo ao seu repositório")
print("2. Execute: streamlit run test_ultra_robust_pdf.py")
print("3. Verifique os logs no console do Streamlit Cloud")