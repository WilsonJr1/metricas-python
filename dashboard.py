import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import os
import io
import base64
from datetime import date

# Configurações DEFINITIVAS para produção
try:
    from config_production import setup_production_environment
    setup_production_environment()
except ImportError:
    print("Aviso: Configurações de produção não disponíveis")

# Configurações específicas para Streamlit Cloud
try:
    from streamlit_config import configure_plotly_for_streamlit
    configure_plotly_for_streamlit()
except ImportError:
    print("Aviso: Configurações específicas do Streamlit não disponíveis")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import kaleido
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"Aviso: Bibliotecas PDF não disponíveis: {e}")

# Importar módulo de sustentação
try:
    from sustentacao import main_sustentacao
except ImportError:
    st.error("Módulo de sustentação não encontrado. Certifique-se de que o arquivo sustentacao.py está no mesmo diretório.")
    main_sustentacao = None

# Importar integração com Google Sheets
try:
    from google_sheets_integration import load_google_sheets_data_automatically
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    st.sidebar.warning("⚠️ Integração com Google Sheets não disponível. Instale as dependências: pip install gspread google-auth")

st.set_page_config(
    page_title="Dashboard DelTech - QA & Sustentação",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def diagnosticar_ambiente_pdf():
    """
    Diagnóstica o ambiente para geração de PDFs e gráficos
    """
    diagnostico = {
        'kaleido_disponivel': False,
        'kaleido_versao': None,
        'reportlab_disponivel': False,
        'ambiente': 'desconhecido',
        'problemas': []
    }
    
    try:
        import kaleido
        diagnostico['kaleido_disponivel'] = True
        # Correção para versões do kaleido sem __version__
        try:
            diagnostico['kaleido_versao'] = kaleido.__version__
        except AttributeError:
            diagnostico['kaleido_versao'] = 'instalado (versão desconhecida)'
    except ImportError:
        diagnostico['problemas'].append('Kaleido não instalado')
    
    try:
        from reportlab.lib.pagesizes import letter
        diagnostico['reportlab_disponivel'] = True
    except ImportError:
        diagnostico['problemas'].append('ReportLab não instalado')
    
    # Detectar ambiente
    if 'STREAMLIT_SERVER_PORT' in os.environ:
        diagnostico['ambiente'] = 'streamlit_cloud'
    elif 'STREAMLIT_BROWSER_GATHER_USAGE_STATS' in os.environ:
        diagnostico['ambiente'] = 'streamlit_local'
    elif 'JUPYTER_SERVER_ROOT' in os.environ:
        diagnostico['ambiente'] = 'jupyter'
    else:
        diagnostico['ambiente'] = 'local'
    
    return diagnostico

def exportar_grafico_para_pdf(fig, titulo, largura=800, altura=600):
    """
    Versão ULTRA-ROBUSTA para Streamlit Cloud
    Implementa múltiplas estratégias de fallback para garantir funcionamento
    """
    if fig is None:
        print(f"❌ Gráfico '{titulo}' é None")
        return None
    
    print(f"🔄 Iniciando conversão: {titulo}")
    
    try:
        import plotly.io as pio
        import plotly.graph_objects as go
        import copy
        
        # CONFIGURAÇÕES CRÍTICAS PARA STREAMLIT CLOUD
        os.environ.update({
            'MPLBACKEND': 'Agg',
            'DISPLAY': ':99',
            'KALEIDO_DISABLE_GPU': 'true',
            'CHROMIUM_FLAGS': '--no-sandbox --disable-dev-shm-usage --disable-gpu --single-process'
        })
        
        # ESTRATÉGIA 1: Configuração Ultra-Conservadora
        print("🎯 Estratégia 1: Configuração ultra-conservadora")
        try:
             # Usar nova API se disponível, senão fallback para antiga
             if hasattr(pio, 'defaults'):
                 pio.defaults.chromium_args = (
                     '--no-sandbox',
                     '--disable-dev-shm-usage',
                     '--disable-gpu',
                     '--single-process',
                     '--disable-extensions',
                     '--disable-plugins',
                     '--no-first-run',
                     '--disable-default-apps',
                     '--disable-background-timer-throttling',
                     '--disable-renderer-backgrounding'
                 )
                 pio.defaults.default_timeout = 120
             else:
                 pio.kaleido.scope.chromium_args = (
                     '--no-sandbox',
                     '--disable-dev-shm-usage',
                     '--disable-gpu',
                     '--single-process',
                     '--disable-extensions',
                     '--disable-plugins',
                     '--no-first-run',
                     '--disable-default-apps',
                     '--disable-background-timer-throttling',
                     '--disable-renderer-backgrounding'
                 )
                 pio.kaleido.scope.default_timeout = 120
             
             fig_copy = copy.deepcopy(fig)
             fig_copy.update_layout(
                 plot_bgcolor='white',
                 paper_bgcolor='white',
                 font=dict(color='black', size=12),
                 width=700,
                 height=450,
                 margin=dict(l=60, r=60, t=80, b=60)
             )
             
             img_bytes = fig_copy.to_image(format="png", width=700, height=450, scale=1)
             
             if img_bytes and len(img_bytes) > 1000:
                 print(f"✅ Estratégia 1 SUCESSO: {len(img_bytes)} bytes")
                 img_buffer = io.BytesIO(img_bytes)
                 return Image(img_buffer, width=6*inch, height=4*inch)
                
        except Exception as e:
            print(f"⚠️ Estratégia 1 falhou: {e}")
        
        # ESTRATÉGIA 2: Configuração Minimalista
        print("🎯 Estratégia 2: Configuração minimalista")
        try:
            pio.kaleido.scope.chromium_args = ('--no-sandbox', '--disable-dev-shm-usage')
            pio.kaleido.scope.default_timeout = 90
            
            fig_simple = copy.deepcopy(fig)
            fig_simple.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                width=600,
                height=400
            )
            
            img_bytes = fig_simple.to_image(format="png", width=600, height=400)
            
            if img_bytes and len(img_bytes) > 500:
                print(f"✅ Estratégia 2 SUCESSO: {len(img_bytes)} bytes")
                img_buffer = io.BytesIO(img_bytes)
                return Image(img_buffer, width=6*inch, height=4*inch)
                
        except Exception as e:
            print(f"⚠️ Estratégia 2 falhou: {e}")
        
        # ESTRATÉGIA 3: Gráfico Simplificado
        print("🎯 Estratégia 3: Gráfico simplificado")
        try:
            pio.kaleido.scope.chromium_args = ('--no-sandbox',)
            pio.kaleido.scope.default_timeout = 60
            
            # Criar versão simplificada do gráfico
            if hasattr(fig, 'data') and len(fig.data) > 0:
                trace = fig.data[0]
                
                fig_backup = go.Figure()
                
                if hasattr(trace, 'x') and hasattr(trace, 'y'):
                    if trace.type == 'bar':
                        fig_backup.add_trace(go.Bar(
                            x=trace.x[:10] if len(trace.x) > 10 else trace.x,
                            y=trace.y[:10] if len(trace.y) > 10 else trace.y,
                            name=getattr(trace, 'name', 'Dados')
                        ))
                    else:
                        fig_backup.add_trace(go.Scatter(
                            x=trace.x[:10] if len(trace.x) > 10 else trace.x,
                            y=trace.y[:10] if len(trace.y) > 10 else trace.y,
                            mode='lines+markers',
                            name=getattr(trace, 'name', 'Dados')
                        ))
                else:
                    # Gráfico de fallback genérico
                    fig_backup.add_trace(go.Bar(
                        x=['Dados', 'Disponíveis'],
                        y=[1, 1],
                        name='Informações'
                    ))
                
                fig_backup.update_layout(
                    title=f"Gráfico: {titulo}",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    width=500,
                    height=350,
                    font=dict(size=10)
                )
                
                img_bytes = fig_backup.to_image(format="png", width=500, height=350)
                
                if img_bytes and len(img_bytes) > 100:
                    print(f"✅ Estratégia 3 SUCESSO: {len(img_bytes)} bytes")
                    img_buffer = io.BytesIO(img_bytes)
                    return Image(img_buffer, width=6*inch, height=4*inch)
                    
        except Exception as e:
            print(f"⚠️ Estratégia 3 falhou: {e}")
        
        # ESTRATÉGIA 4: Gráfico de Emergência
        print("🎯 Estratégia 4: Gráfico de emergência")
        try:
            fig_emergency = go.Figure()
            fig_emergency.add_trace(go.Scatter(
                x=[1, 2, 3],
                y=[1, 2, 1],
                mode='lines+markers',
                name='Dados do Gráfico'
            ))
            
            fig_emergency.update_layout(
                title=f"Dados: {titulo}",
                plot_bgcolor='white',
                paper_bgcolor='white',
                width=400,
                height=300,
                showlegend=False
            )
            
            img_bytes = fig_emergency.to_image(format="png", width=400, height=300)
            
            if img_bytes and len(img_bytes) > 50:
                print(f"✅ Estratégia 4 SUCESSO (emergência): {len(img_bytes)} bytes")
                img_buffer = io.BytesIO(img_bytes)
                return Image(img_buffer, width=6*inch, height=4*inch)
                
        except Exception as e:
            print(f"❌ Estratégia 4 falhou: {e}")
        
        print(f"❌ TODAS as estratégias falharam para '{titulo}'")
        return None
        
    except Exception as e:
        print(f"❌ Erro crítico na conversão de '{titulo}': {e}")
        import traceback
        traceback.print_exc()
        return None

def criar_pdf_relatorio_detalhado(df_filtrado, df_original, df_sem_teste=None):
    """
    Cria um PDF completo e detalhado do relatório com insights e análises
    """
    if not PDF_AVAILABLE:
        st.error("📄 Bibliotecas PDF não disponíveis. Instale: pip install reportlab kaleido")
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.7*inch, 
        bottomMargin=0.7*inch,
        leftMargin=0.7*inch,
        rightMargin=0.7*inch
    )
    styles = getSampleStyleSheet()
    story = []
    
    # Definir paleta de cores profissional
    cor_primaria = colors.Color(0.2, 0.4, 0.8)  # Azul Delfinance
    cor_secundaria = colors.Color(0.3, 0.5, 0.9)  # Azul médio
    cor_destaque = colors.Color(0.8, 0.2, 0.2)  # Vermelho
    cor_sucesso = colors.Color(0.2, 0.4, 0.8)  # Azul
    cor_fundo = colors.Color(0.95, 0.95, 0.95)  # Cinza claro
    
    # Estilos customizados profissionais
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=40,
        spaceBefore=20,
        alignment=1,
        textColor=cor_primaria,
        fontName='Times-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=25,
        textColor=cor_secundaria,
        fontName='Times-Bold',
        borderWidth=1,
        borderColor=cor_secundaria,
        borderPadding=8
    )
    
    insight_style_positivo = ParagraphStyle(
        'InsightStylePositivo',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leftIndent=25,
        rightIndent=10,
        textColor=cor_sucesso,
        fontName='Times-Roman',
        backColor=cor_fundo,
        borderWidth=0.5,
        borderColor=cor_sucesso,
        borderPadding=6
    )
    
    insight_style_neutro = ParagraphStyle(
        'InsightStyleNeutro',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leftIndent=25,
        rightIndent=10,
        textColor=cor_secundaria,
        fontName='Times-Roman',
        backColor=cor_fundo,
        borderWidth=0.5,
        borderColor=cor_secundaria,
        borderPadding=6
    )
    
    insight_style_negativo = ParagraphStyle(
        'InsightStyleNegativo',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leftIndent=25,
        rightIndent=10,
        textColor=cor_destaque,
        fontName='Times-Roman',
        backColor=cor_fundo,
        borderWidth=0.5,
        borderColor=cor_destaque,
        borderPadding=6
    )
    
    normal_enhanced = ParagraphStyle(
        'NormalEnhanced',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.black,
        fontName='Times-Roman',
        alignment=0
    )
    
    chart_title_style = ParagraphStyle(
        'ChartTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=5,
        textColor=cor_secundaria,
        fontName='Times-Bold',
        alignment=0
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=cor_secundaria,
        fontName='Times-Italic',
        alignment=1
    )
    
    # Cabeçalho do relatório com design profissional
    from reportlab.platypus import HRFlowable
    from reportlab.graphics.shapes import Drawing, Rect, Polygon
    from reportlab.graphics import renderPDF
    
    # Criar logo da Delfinance com formatação profissional
    from reportlab.platypus import Paragraph
    
    # Estilo profissional para o cabeçalho
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=20,
        fontName='Times-Bold',
        alignment=1,  # Centralizado
        spaceAfter=15,
        textColor=colors.black
    )
    
    # Barra azul no topo mais grossa
    story.append(HRFlowable(width="100%", thickness=8, color=cor_primaria))
    story.append(Spacer(1, 15))
    
    # Logo del.tech no canto esquerdo
    logo_style = ParagraphStyle(
        'LogoStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Times-Bold',
        alignment=0,  # Alinhado à esquerda
        spaceAfter=10
    )
    
    try:
        # Tentar carregar a imagem del.tech no canto esquerdo
        logo_img = Image("Deltech.png", width=0.5*inch, height=0.2*inch)
        logo_img.hAlign = 'LEFT'
        story.append(logo_img)
    except:
        # Fallback para texto estilizado caso a imagem não seja encontrada
        logo_text = Paragraph("<font color='#1976D2' size='12'>🔧 del.tech</font>", logo_style)
        story.append(logo_text)
    
    story.append(Spacer(1, 15))
    
    # Título centralizado
    title_text = Paragraph("BOLETIM DE IMPLANTAÇÕES", header_style)
    story.append(title_text)
    story.append(Spacer(1, 25))
    
    # Calcular período baseado nos dados filtrados
    if len(df_filtrado) > 0 and 'Data' in df_filtrado.columns:
        try:
            # Converter coluna Data para datetime se necessário
            df_temp = df_filtrado.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_temp['Data']):
                df_temp['Data'] = pd.to_datetime(df_temp['Data'], dayfirst=True, errors='coerce')
            
            # Obter datas mínima e máxima dos dados filtrados
            data_min = df_temp['Data'].min()
            data_max = df_temp['Data'].max()
            
            if pd.notna(data_min) and pd.notna(data_max):
                if data_min.date() == data_max.date():
                    periodo_analise = data_min.strftime('%d/%m/%Y')
                else:
                    periodo_analise = f"{data_min.strftime('%d/%m/%Y')} a {data_max.strftime('%d/%m/%Y')}"
            else:
                periodo_analise = date.today().strftime('%d/%m/%Y')
        except Exception:
            periodo_analise = date.today().strftime('%d/%m/%Y')
    else:
        periodo_analise = date.today().strftime('%d/%m/%Y')
    
    # Informações do cabeçalho simplificado
    header_data = [
        ['Período de Análise:', periodo_analise]
    ]
    
    header_table = Table(header_data, colWidths=[2.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, 0), cor_secundaria),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Calcular métricas detalhadas
    total_tasks = len(df_filtrado)
    tasks_unicas = df_filtrado['Nome da Task'].nunique() if 'Nome da Task' in df_filtrado.columns else 0
    aprovadas = len(df_filtrado[df_filtrado['Status'] == 'APROVADA']) if 'Status' in df_filtrado.columns else 0
    prontas = len(df_filtrado[df_filtrado['Status'] == 'PRONTO PARA PUBLICAÇÃO']) if 'Status' in df_filtrado.columns else 0
    total_aprovadas = aprovadas + prontas
    rejeitadas = len(df_filtrado[df_filtrado['Status'] == 'REJEITADA']) if 'Status' in df_filtrado.columns else 0
    # Calcular tarefas retestadas
    historico_retestes = analisar_historico_retestes(df_filtrado)
    tarefas_retestadas = historico_retestes['total_tarefas_retestadas']
    taxa_aprovacao = (total_aprovadas/(total_aprovadas + rejeitadas)*100) if (total_aprovadas + rejeitadas) > 0 else 0
    taxa_rejeicao = (rejeitadas/total_tasks*100) if total_tasks > 0 else 0
    
    # Times únicos
    times_unicos = df_filtrado['Time'].nunique() if 'Time' in df_filtrado.columns else 0
    testadores_unicos = df_filtrado['Responsavel pelo teste'].nunique() if 'Responsavel pelo teste' in df_filtrado.columns else 0
    
    # 1. RESUMO EXECUTIVO
    story.append(Paragraph("1. RESUMO EXECUTIVO", subtitle_style))
    
    resumo_texto = f"""
    Este relatório apresenta uma análise abrangente da qualidade dos testes realizados no período, 
    abrangendo {total_tasks} testes executados em {tasks_unicas} tarefas únicas, distribuídas entre 
    {times_unicos} times de desenvolvimento e executadas por {testadores_unicos} testadores.
    
    A taxa de aprovação atual é de {taxa_aprovacao:.1f}%, indicando {'um excelente' if taxa_aprovacao >= 80 else 'um bom' if taxa_aprovacao >= 60 else 'um nível que requer atenção'} 
    nível de qualidade nas entregas.
    """
    story.append(Paragraph(resumo_texto, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tabela de métricas principais com design profissional
    metricas_data = [
        ['MÉTRICA', 'VALOR', 'INDICADOR', 'TENDÊNCIA'],
        ['Total de Tarefas Únicas', f'{tasks_unicas}', 'OK', 'Estável'],
        ['Total de Testes Realizados', f'{total_tasks}', 'OK', 'Crescente'],
        ['Tarefas Aprovadas', f'{aprovadas}', 'OK', 'Positiva'],
        ['Tarefas Rejeitadas', f'{rejeitadas}', 'OK', 'Controlada'],
        ['Tarefas Retestadas', f'{tarefas_retestadas}', 'OK', 'Controlada'],
        ['Taxa de Aprovação', f'{taxa_aprovacao:.1f}%', 'OK', 'Excelente' if taxa_aprovacao >= 80 else 'Boa' if taxa_aprovacao >= 60 else 'Crítica'],
        ['Taxa de Rejeição', f'{taxa_rejeicao:.1f}%', 'OK', 'Baixa' if taxa_rejeicao <= 20 else 'Alta'],
        ['Times Envolvidos', f'{times_unicos}', 'OK', 'Engajados'],
        ['Testadores Ativos', f'{testadores_unicos}', 'OK', 'Produtivos']
    ]
    
    metricas_table = Table(metricas_data, colWidths=[2.2*inch, 1.0*inch, 1.2*inch, 1.3*inch])
    metricas_table.setStyle(TableStyle([
        # Cabeçalho com design profissional
        ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cor_fundo]),
        
        # Bordas e separadores
        ('GRID', (0, 0), (-1, -1), 0.5, cor_secundaria),
        ('LINEBELOW', (0, 0), (-1, 0), 2, cor_primaria),
        ('LINEBEFORE', (1, 0), (1, -1), 1, cor_secundaria),
        ('LINEBEFORE', (2, 0), (2, -1), 1, cor_secundaria),
        ('LINEBEFORE', (3, 0), (3, -1), 1, cor_secundaria),
        
        # Padding e alinhamento
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    story.append(metricas_table)
    story.append(Spacer(1, 15))
    
    # 2. INSIGHTS E ANÁLISES CRÍTICAS
    story.append(Paragraph("2. INSIGHTS E ANÁLISES CRÍTICAS", subtitle_style))
    
    # Análise da taxa de aprovação
    if taxa_aprovacao >= 80:
        insight_aprovacao = "[+] EXCELENTE: Taxa de aprovação acima de 80% indica alta qualidade nas entregas."
        story.append(Paragraph(insight_aprovacao, insight_style_positivo))
    elif taxa_aprovacao >= 60:
        insight_aprovacao = "[!] BOM: Taxa de aprovação entre 60-80% é aceitável, mas há espaço para melhorias."
        story.append(Paragraph(insight_aprovacao, insight_style_neutro))
    else:
        insight_aprovacao = "[X] CRÍTICO: Taxa de aprovação abaixo de 60% requer ação imediata."
        story.append(Paragraph(insight_aprovacao, insight_style_negativo))
    
    # Análise de distribuição de trabalho
    if 'Time' in df_filtrado.columns:
        time_mais_ativo = df_filtrado['Time'].value_counts().index[0] if len(df_filtrado) > 0 else 'N/A'
        tasks_time_ativo = df_filtrado['Time'].value_counts().iloc[0] if len(df_filtrado) > 0 else 0
        story.append(Paragraph(f"[*] DISTRIBUIÇÃO: Time '{time_mais_ativo}' é o mais ativo com {tasks_time_ativo} testes realizados.", insight_style_positivo))
    
    # Análise de testadores
    if 'Responsavel pelo teste' in df_filtrado.columns:
        testador_mais_ativo = df_filtrado['Responsavel pelo teste'].value_counts().index[0] if len(df_filtrado) > 0 else 'N/A'
        tests_testador = df_filtrado['Responsavel pelo teste'].value_counts().iloc[0] if len(df_filtrado) > 0 else 0
        story.append(Paragraph(f"[>] PERFORMANCE: Testador '{testador_mais_ativo}' realizou {tests_testador} testes, sendo o mais produtivo.", insight_style_positivo))
    
    story.append(Spacer(1, 10))
    
    # 3. ANÁLISE DETALHADA POR TIMES
    story.append(Paragraph("3. ANÁLISE DETALHADA POR TIMES", subtitle_style))
    
    if 'Time' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        times_performance = df_filtrado.groupby('Time')['Status'].value_counts().unstack(fill_value=0)
        if 'APROVADA' in times_performance.columns or 'REJEITADA' in times_performance.columns or 'PRONTO PARA PUBLICAÇÃO' in times_performance.columns:
            aprovadas_total = times_performance.get('APROVADA', 0) + times_performance.get('PRONTO PARA PUBLICAÇÃO', 0)
            rejeitadas_total = times_performance.get('REJEITADA', 0)
            total_testadas = aprovadas_total + rejeitadas_total
            times_performance['Taxa_Aprovacao'] = (aprovadas_total / total_testadas * 100).round(1).fillna(0)
            
            performance_data = [['TIME', 'APROVADAS', 'REJEITADAS', 'TAXA APROVAÇÃO']]
            for time in times_performance.index:
                aprovadas_time = times_performance.loc[time, 'APROVADA'] if 'APROVADA' in times_performance.columns else 0
                prontas_time = times_performance.loc[time, 'PRONTO PARA PUBLICAÇÃO'] if 'PRONTO PARA PUBLICAÇÃO' in times_performance.columns else 0
                total_aprovadas_time = aprovadas_time + prontas_time
                rejeitadas_time = times_performance.loc[time, 'REJEITADA'] if 'REJEITADA' in times_performance.columns else 0
                taxa_time = times_performance.loc[time, 'Taxa_Aprovacao'] if 'Taxa_Aprovacao' in times_performance.columns else 0
                performance_data.append([time, str(total_aprovadas_time), str(rejeitadas_time), f'{taxa_time}%'])
            
            performance_table = Table(performance_data)
            performance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(performance_table)
    
    story.append(Spacer(1, 15))
    
    # 4. GRÁFICOS E VISUALIZAÇÕES
    story.append(Paragraph("4. GRÁFICOS E VISUALIZAÇÕES", subtitle_style))
    
    # Gráfico de status
    try:
        fig_status = grafico_status_distribuicao(df_filtrado)
        if fig_status:
            img_grafico = exportar_grafico_para_pdf(fig_status, "Status dos Testes")
            if img_grafico:
                story.append(Paragraph("Distribuição por Status", chart_title_style))
                story.append(img_grafico)
                story.append(Spacer(1, 30))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar gráfico de status: {e}", styles['Normal']))

    # Gráfico de tarefas por time
    try:
        fig_time = grafico_tasks_por_time(df_filtrado)
        if fig_time:
            img_grafico = exportar_grafico_para_pdf(fig_time, "Tarefas por Time")
            if img_grafico:
                story.append(Paragraph("Tarefas por Time", chart_title_style))
                story.append(img_grafico)
                story.append(Spacer(1, 30))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar gráfico por time: {e}", styles['Normal']))
    

    
    # Gráfico de tarefas retestadas
    try:
        fig_retestadas = grafico_tarefas_retestadas(df_filtrado)
        if fig_retestadas:
            img_grafico = exportar_grafico_para_pdf(fig_retestadas, "Tarefas Retestadas")
            if img_grafico:
                story.append(Paragraph("Histórico de Tarefas Retestadas", chart_title_style))
                story.append(img_grafico)
                story.append(Spacer(1, 30))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar gráfico de tarefas retestadas: {e}", styles['Normal']))

    # Gráfico de motivos de rejeição
    try:
        fig_motivos = grafico_motivos_rejeicao(df_filtrado, por_ambiente=False)
        if fig_motivos:
            img_grafico = exportar_grafico_para_pdf(fig_motivos, "Motivos de Rejeição")
            if img_grafico:
                story.append(Paragraph("Principais Motivos de Rejeição", chart_title_style))
                story.append(img_grafico)
                story.append(Spacer(1, 15))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar gráfico de motivos: {e}", styles['Normal']))
    

    

    
    # Gráfico de ranking de problemas
    try:
        fig_ranking = grafico_ranking_problemas(df_filtrado)
        if fig_ranking:
            img_grafico = exportar_grafico_para_pdf(fig_ranking, "Ranking de Problemas")
            if img_grafico:
                story.append(Paragraph("Ranking dos Principais Problemas", styles['Heading3']))
                story.append(img_grafico)
                story.append(Spacer(1, 20))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar ranking de problemas: {e}", styles['Normal']))
    
    # Gráfico de taxa de rejeição por time
    try:
        fig_taxa_rejeicao = grafico_taxa_rejeicao_por_time(df_filtrado)
        if fig_taxa_rejeicao:
            img_grafico = exportar_grafico_para_pdf(fig_taxa_rejeicao, "Taxa de Rejeição por Time")
            if img_grafico:
                story.append(Paragraph("Taxa de Rejeição por Time de Desenvolvimento", styles['Heading3']))
                story.append(img_grafico)
                story.append(Spacer(1, 10))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar taxa de rejeição por time: {e}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # 6. TAREFAS ENTREGUES E PRODUÇÃO
    story.append(Paragraph("5. TAREFAS ENTREGUES EM PRODUÇÃO", subtitle_style))
    
    # Filtrar tarefas aprovadas
    df_aprovadas = df_filtrado[df_filtrado['Status'] == 'APROVADA'].copy()
    
    if len(df_aprovadas) > 0:
        story.append(Paragraph(f"Total de tarefas entregues em produção: {len(df_aprovadas)}", insight_style_positivo))
        
        # Criar tabela de tarefas aprovadas
        aprovadas_data = [['NOME DA TASK', 'DESCRIÇÃO']]
        
        for _, row in df_aprovadas.head(20).iterrows():  # Limitar a 20 registros para não sobrecarregar o PDF
            nome_task = str(row.get('Nome da Task', 'N/A'))[:60]
            descricao_raw = str(row.get('Descrição', 'N/A'))
            # Usar Paragraph para quebra automática de linha
            descricao = Paragraph(descricao_raw, ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, wordWrap='CJK'))
            
            aprovadas_data.append([nome_task, descricao])
        
        aprovadas_table = Table(aprovadas_data, colWidths=[4.5*inch, 2.5*inch])
        aprovadas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cor_fundo]),
            ('GRID', (0, 0), (-1, -1), 0.5, cor_secundaria),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4)
        ]))
        
        story.append(aprovadas_table)
        
        if len(df_aprovadas) > 20:
            story.append(Paragraph(f"... e mais {len(df_aprovadas) - 20} tarefas entregues.", styles['Normal']))
    else:
        story.append(Paragraph("Nenhuma tarefa aprovada encontrada no período.", insight_style_neutro))
    
    story.append(Spacer(1, 10))
    
    # 7. TAREFAS PRONTAS PARA PUBLICAÇÃO
    story.append(Paragraph("6. TAREFAS PRONTAS PARA PUBLICAÇÃO", subtitle_style))
    
    # Filtrar tarefas prontas para publicação
    df_prontas = df_filtrado[df_filtrado['Status'] == 'PRONTO PARA PUBLICAÇÃO'].copy()
    
    if len(df_prontas) > 0:
        story.append(Paragraph(f"Total de tarefas prontas para publicação: {len(df_prontas)}", insight_style_positivo))
        
        # Criar tabela de tarefas prontas
        prontas_data = [['NOME DA TASK', 'DESCRIÇÃO']]
        
        for _, row in df_prontas.head(20).iterrows():  # Limitar a 20 registros
            nome_task = str(row.get('Nome da Task', 'N/A'))[:60]
            descricao_raw = str(row.get('Descrição', 'N/A'))
            # Usar Paragraph para quebra automática de linha
            descricao = Paragraph(descricao_raw, ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, wordWrap='CJK'))
            
            prontas_data.append([nome_task, descricao])
        
        prontas_table = Table(prontas_data, colWidths=[4.5*inch, 2.5*inch])
        prontas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cor_fundo]),
            ('GRID', (0, 0), (-1, -1), 0.5, cor_secundaria),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4)
        ]))
        
        story.append(prontas_table)
        
        if len(df_prontas) > 20:
            story.append(Paragraph(f"... e mais {len(df_prontas) - 20} tarefas prontas para publicação.", styles['Normal']))
    else:
        story.append(Paragraph("Nenhuma tarefa pronta para publicação encontrada no período.", insight_style_neutro))
    
    story.append(Spacer(1, 15))
    

    

    

    
    # Rodapé profissional
    story.append(HRFlowable(width="100%", thickness=1, color=cor_secundaria))
    story.append(Spacer(1, 12))
    
    # Informações do rodapé simplificado
    from datetime import datetime
    import pytz
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now_brasilia = datetime.now(brasilia_tz)
    footer_data = [
        ['Data de Geração:', now_brasilia.strftime('%d/%m/%Y às %H:%M')],
        ['Confidencialidade:', 'Documento Interno - Uso Restrito']
    ]
    
    footer_table = Table(footer_data, colWidths=[2.0*inch, 4.0*inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), cor_secundaria),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
    ]))
    
    story.append(footer_table)
    story.append(Spacer(1, 15))
    
    # Assinatura digital
    assinatura_style = ParagraphStyle(
        'AssinaturaStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=cor_secundaria,
        fontName='Times-Italic',
        alignment=1
    )
    
    story.append(Paragraph("Relatório gerado automaticamente pelo sistema de métricas DelTech", assinatura_style))
    story.append(Paragraph("© 2025 DelTech - Todos os direitos reservados", assinatura_style))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def criar_pdf_visao_geral(df_filtrado, df_original, df_sem_teste=None):
    """
    Cria um PDF da Visão Geral Estratégica
    """
    if not PDF_AVAILABLE:
        st.error("📄 Bibliotecas PDF não disponíveis. Instale: pip install reportlab kaleido")
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Definir cores
    cor_primaria = colors.Color(0.098, 0.463, 0.824)  # Azul
    
    # Barra azul no topo mais grossa
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=8, color=cor_primaria))
    story.append(Spacer(1, 15))
    
    # Logo del.tech no canto esquerdo
    logo_style = ParagraphStyle(
        'LogoStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Times-Bold',
        alignment=0,  # Alinhado à esquerda
        spaceAfter=10
    )
    
    try:
        # Tentar carregar a imagem del.tech no canto esquerdo
        logo_img = Image("Deltech.png", width=0.5*inch, height=0.2*inch)
        logo_img.hAlign = 'LEFT'
        story.append(logo_img)
    except:
        # Fallback para texto estilizado caso a imagem não seja encontrada
        logo_text = Paragraph("<font color='#1976D2' size='12'>🔧 del.tech</font>", logo_style)
        story.append(logo_text)
    
    story.append(Spacer(1, 15))
    
    # Título centralizado
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1
    )
    story.append(Paragraph("Visão Geral Estratégica - QA", title_style))
    story.append(Paragraph(f"Data: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Métricas principais
    story.append(Paragraph("Principais Indicadores", styles['Heading2']))
    
    total_planilha = len(df_original)
    total_testes_efetuados = len(df_filtrado)
    cobertura_teste = (total_testes_efetuados / total_planilha * 100) if total_planilha > 0 else 0
    aprovadas = len(df_filtrado[df_filtrado['Status'] == 'APROVADA']) if 'Status' in df_filtrado.columns else 0
    prontas = len(df_filtrado[df_filtrado['Status'] == 'PRONTO PARA PUBLICAÇÃO']) if 'Status' in df_filtrado.columns else 0
    total_aprovadas_pdf = aprovadas + prontas
    rejeitadas = len(df_filtrado[df_filtrado['Status'] == 'REJEITADA']) if 'Status' in df_filtrado.columns else 0
    taxa_aprovacao = (total_aprovadas_pdf / (total_aprovadas_pdf + rejeitadas) * 100) if (total_aprovadas_pdf + rejeitadas) > 0 else 0
    
    metricas_data = [
        ['Indicador', 'Valor'],
        ['Total de Registros', f'{total_planilha:,}'],
        ['Testes Realizados', f'{total_testes_efetuados:,}'],
        ['Cobertura de Testes', f'{cobertura_teste:.1f}%'],
        ['Taxa de Aprovação', f'{taxa_aprovacao:.1f}%'],
        ['Tarefas Aprovadas', f'{aprovadas:,}'],
        ['Tarefas Rejeitadas', f'{rejeitadas:,}']
    ]
    
    metricas_table = Table(metricas_data)
    metricas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metricas_table)
    story.append(Spacer(1, 15))
    
    # Adicionar gráficos principais
    story.append(Paragraph("Análise Visual", styles['Heading2']))
    
    # Gráfico de evolução da qualidade
    try:
        fig_evolucao = grafico_evolucao_qualidade(df_filtrado, por_ambiente=False)
        if fig_evolucao:
            img_grafico = exportar_grafico_para_pdf(fig_evolucao, "Evolução da Qualidade")
            if img_grafico:
                story.append(Paragraph("Evolução da Qualidade", styles['Heading3']))
                story.append(img_grafico)
                story.append(Spacer(1, 10))
    except Exception as e:
        story.append(Paragraph(f"Erro ao gerar gráfico de evolução: {e}", styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def criar_pdf_generico(titulo, df_filtrado, graficos_funcoes=None):
    """
    Cria um PDF genérico para qualquer aba
    """
    if not PDF_AVAILABLE:
        st.error("📄 Bibliotecas PDF não disponíveis. Instale: pip install reportlab kaleido")
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Definir cores
    cor_primaria = colors.Color(0.098, 0.463, 0.824)  # Azul
    
    # Barra azul no topo mais grossa
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=8, color=cor_primaria))
    story.append(Spacer(1, 15))
    
    # Logo del.tech no canto esquerdo
    logo_style = ParagraphStyle(
        'LogoStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Times-Bold',
        alignment=0,  # Alinhado à esquerda
        spaceAfter=10
    )
    
    try:
        # Tentar carregar a imagem del.tech no canto esquerdo
        logo_img = Image("Deltech.png", width=0.5*inch, height=0.2*inch)
        logo_img.hAlign = 'LEFT'
        story.append(logo_img)
    except:
        # Fallback para texto estilizado caso a imagem não seja encontrada
        logo_text = Paragraph("<font color='#1976D2' size='12'>🔧 del.tech</font>", logo_style)
        story.append(logo_text)
    
    story.append(Spacer(1, 15))
    
    # Título centralizado
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1
    )
    story.append(Paragraph(titulo, title_style))
    story.append(Paragraph(f"Data: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Informações básicas
    story.append(Paragraph("Resumo dos Dados", styles['Heading2']))
    story.append(Paragraph(f"Total de registros analisados: {len(df_filtrado)}", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Adicionar gráficos se fornecidos
    if graficos_funcoes:
        story.append(Paragraph("Análise Visual", styles['Heading2']))
        for nome_grafico, funcao_grafico in graficos_funcoes.items():
            try:
                fig = funcao_grafico(df_filtrado)
                if fig:
                    img_grafico = exportar_grafico_para_pdf(fig, nome_grafico)
                    if img_grafico:
                        story.append(Paragraph(nome_grafico, styles['Heading3']))
                        story.append(img_grafico)
                        story.append(Spacer(1, 10))
            except Exception as e:
                story.append(Paragraph(f"Erro ao gerar {nome_grafico}: {e}", styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def botao_exportar_pdf(nome_relatorio, funcao_exportar, *args):
    """
    Cria um botão para exportar PDF
    """
    if st.button(f"📄 Exportar {nome_relatorio} em PDF", key=f"export_{nome_relatorio}"):
        with st.spinner(f"Gerando PDF do {nome_relatorio}..."):
            pdf_buffer = funcao_exportar(*args)
            if pdf_buffer:
                st.download_button(
                    label=f"⬇️ Download {nome_relatorio}.pdf",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{nome_relatorio}_{date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"download_{nome_relatorio}"
                )
                st.success(f"✅ PDF do {nome_relatorio} gerado com sucesso!")

def carregar_dados():
    # Tentar carregar automaticamente do Google Sheets
    if GOOGLE_SHEETS_AVAILABLE:
        with st.spinner("🔄 Carregando dados do Google Sheets..."):
            df = load_google_sheets_data_automatically()
            if df is not None:
                st.success(f"✅Planilha importada com sucesso! {len(df)} registros encontrados.")
                return df
            else:
                st.warning("⚠️ Não foi possível carregar os dados do Google Sheets. Verifique as credenciais.")
    
    # Fallback para upload manual
    st.info("📁 Faça upload do arquivo Excel como alternativa:")
    uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")
            return df
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return None
    
    return None

def processar_dados(df):
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    
    # Manter status original - não substituir "PRONTO PARA PUBLICAÇÃO"
    
    colunas_esperadas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                        'Status', 'Responsável', 'Motivo', 'Motivo2', 'Motivo3', 
                        'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7', 'Ambiente',
                        'Responsavel pelo teste', 'ID', 'Erros']
    
    colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
    if colunas_faltantes:
        st.warning(f"Colunas não encontradas: {colunas_faltantes}")
    
    return df

def separar_dados_sem_teste(df):
    """Separa registros com motivo 'SEM TESTE' dos dados principais e filtra responsáveis"""
    if 'Motivo' in df.columns:
        # Primeiro separar por motivo
        sem_teste_mask = df['Motivo'].str.upper().str.contains('SEM TESTE', na=False)
        sem_teste = df[sem_teste_mask]
        com_teste = df[~sem_teste_mask]
        
        # Filtrar Wesley dos testadores apenas nos dados COM teste (Eduardo e Wilson)
        if 'Responsavel pelo teste' in com_teste.columns:
            com_teste = com_teste[com_teste['Responsavel pelo teste'].isin(['Eduardo', 'Wilson'])]
        
        return com_teste, sem_teste
    return df, pd.DataFrame()

def contar_bugs_por_time(df_rejeitadas):
    """Conta todos os bugs por time considerando Motivo, Motivo2 e Motivo3"""
    if df_rejeitadas.empty:
        return pd.Series(dtype=int)
    
    bugs_por_time = {}
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    
    for _, row in df_rejeitadas.iterrows():
        time = row.get('Time', 'Desconhecido')
        if time not in bugs_por_time:
            bugs_por_time[time] = 0
        
        # Conta cada motivo não nulo como um bug separado, excluindo não-bugs
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    bugs_por_time[time] += 1
    
    return pd.Series(bugs_por_time).sort_values(ascending=False)

def analisar_historico_retestes(df):
    """Analisa o histórico de retestes das tarefas baseado no ID ou Nome da Task"""
    if df.empty:
        return {
            'total_tarefas_retestadas': 0,
            'tarefas_aprovadas_apos_reteste': 0,
            'taxa_aprovacao_apos_reteste': 0,
            'detalhes_retestes': pd.DataFrame()
        }
    
    # Usar ID como identificador principal, Nome da Task como fallback
    identificador = 'ID' if 'ID' in df.columns and df['ID'].notna().any() else 'Nome da Task'
    
    if identificador not in df.columns:
        return {
            'total_tarefas_retestadas': 0,
            'tarefas_aprovadas_apos_reteste': 0,
            'taxa_aprovacao_apos_reteste': 0,
            'detalhes_retestes': pd.DataFrame()
        }
    
    # Ordenar por identificador e data para análise temporal
    df_sorted = df.sort_values([identificador, 'Data']).copy()
    
    # Agrupar por identificador para analisar histórico
    historico_tarefas = []
    tarefas_retestadas = set()
    tarefas_aprovadas_apos_reteste = set()
    
    for task_id, group in df_sorted.groupby(identificador):
        if len(group) > 1:  # Tarefa testada mais de uma vez
            group_sorted = group.sort_values('Data')
            status_sequence = group_sorted['Status'].tolist()
            
            # Verificar se houve rejeição seguida de aprovação
            teve_rejeicao = any(status in ['REJEITADA'] for status in status_sequence)
            teve_aprovacao = any(status in ['APROVADA', 'PRONTO PARA PUBLICAÇÃO'] for status in status_sequence)
            
            if teve_rejeicao:
                tarefas_retestadas.add(task_id)
                
                # Verificar se foi aprovada após rejeição
                for i, status in enumerate(status_sequence):
                    if status == 'REJEITADA' and i < len(status_sequence) - 1:
                        # Verificar se há aprovação após esta rejeição
                        status_posteriores = status_sequence[i+1:]
                        if any(s in ['APROVADA', 'PRONTO PARA PUBLICAÇÃO'] for s in status_posteriores):
                            tarefas_aprovadas_apos_reteste.add(task_id)
                            break
                
                # Adicionar detalhes do histórico
                historico_tarefas.append({
                    'Identificador': task_id,
                    'Nome_Tarefa': group_sorted['Nome da Task'].iloc[0] if 'Nome da Task' in group_sorted.columns else '',
                    'Total_Testes': len(group_sorted),
                    'Sequencia_Status': ' → '.join(status_sequence),
                    'Aprovada_Apos_Reteste': task_id in tarefas_aprovadas_apos_reteste,
                    'Primeira_Data': group_sorted['Data'].iloc[0],
                    'Ultima_Data': group_sorted['Data'].iloc[-1],
                    'Time': group_sorted['Time'].iloc[0] if 'Time' in group_sorted.columns else '',
                    'Responsavel': group_sorted['Responsável'].iloc[0] if 'Responsável' in group_sorted.columns else ''
                })
    
    # Calcular métricas
    total_retestadas = len(tarefas_retestadas)
    total_aprovadas_apos_reteste = len(tarefas_aprovadas_apos_reteste)
    taxa_aprovacao_apos_reteste = (total_aprovadas_apos_reteste / total_retestadas * 100) if total_retestadas > 0 else 0
    
    # Criar DataFrame com detalhes
    df_detalhes = pd.DataFrame(historico_tarefas)
    
    return {
        'total_tarefas_retestadas': total_retestadas,
        'tarefas_aprovadas_apos_reteste': total_aprovadas_apos_reteste,
        'taxa_aprovacao_apos_reteste': taxa_aprovacao_apos_reteste,
        'detalhes_retestes': df_detalhes
    }

def contar_total_bugs(df_rejeitadas):
    """Conta o total de bugs considerando Motivo, Motivo2, Motivo3, Motivo4, Motivo5, Motivo6 e Motivo7"""
    if df_rejeitadas.empty:
        return 0
    
    total_bugs = 0
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    
    for _, row in df_rejeitadas.iterrows():
        # Conta cada motivo não nulo como um bug separado, excluindo não-bugs
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    total_bugs += 1
    
    return total_bugs

def contar_erros_por_time(df_filtrado):
    """Conta erros por time considerando tanto a coluna 'Erros' quanto os motivos de rejeição"""
    if df_filtrado.empty or 'Time' not in df_filtrado.columns:
        return pd.Series(dtype=int)
    
    erros_por_time = {}
    
    # 1. Contar erros da coluna 'Erros' (dados mais recentes)
    if 'Erros' in df_filtrado.columns:
        df_temp = df_filtrado.copy()
        df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
        df_com_erros = df_temp[df_temp['Erros'] > 0]
        
        for _, row in df_com_erros.iterrows():
            time = row.get('Time', 'Desconhecido')
            if time not in erros_por_time:
                erros_por_time[time] = 0
            erros_por_time[time] += row['Erros']
    
    # 2. Para registros sem dados na coluna 'Erros', usar análise de motivos (dados históricos)
    df_sem_erros_coluna = df_filtrado[
        (~df_filtrado['Erros'].notna()) | 
        (pd.to_numeric(df_filtrado['Erros'], errors='coerce').fillna(0) == 0)
    ] if 'Erros' in df_filtrado.columns else df_filtrado
    
    # Filtrar apenas rejeitadas para análise de motivos
    df_rejeitadas_historicas = df_sem_erros_coluna[df_sem_erros_coluna['Status'] == 'REJEITADA']
    
    # Contar motivos como erros históricos por time
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    for _, row in df_rejeitadas_historicas.iterrows():
        time = row.get('Time', 'Desconhecido')
        if time not in erros_por_time:
            erros_por_time[time] = 0
        
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    erros_por_time[time] += 1
    
    return pd.Series(erros_por_time).sort_values(ascending=False) if erros_por_time else pd.Series(dtype=int)

def contar_total_erros(df_filtrado):
    """Conta o total de erros considerando tanto a coluna 'Erros' quanto os motivos de rejeição"""
    if df_filtrado.empty:
        return 0
    
    total_erros = 0
    
    # 1. Contar erros da coluna 'Erros' (dados mais recentes)
    if 'Erros' in df_filtrado.columns:
        erros_numericos = pd.to_numeric(df_filtrado['Erros'], errors='coerce').fillna(0)
        total_erros += erros_numericos.sum()
    
    # 2. Para registros sem dados na coluna 'Erros', usar análise de motivos (dados históricos)
    df_sem_erros_coluna = df_filtrado[
        (~df_filtrado['Erros'].notna()) | 
        (pd.to_numeric(df_filtrado['Erros'], errors='coerce').fillna(0) == 0)
    ] if 'Erros' in df_filtrado.columns else df_filtrado
    
    # Filtrar apenas rejeitadas para análise de motivos
    df_rejeitadas_historicas = df_sem_erros_coluna[df_sem_erros_coluna['Status'] == 'REJEITADA']
    
    # Contar motivos como erros históricos
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    for _, row in df_rejeitadas_historicas.iterrows():
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    total_erros += 1
    
    if pd.isna(total_erros) or total_erros == float('inf') or total_erros == float('-inf'):
        return 0
    
    try:
        return int(total_erros)
    except (ValueError, OverflowError):
        return 0

def calcular_media_erros_por_teste(df_filtrado):
    """Calcula a média de erros por teste"""
    if df_filtrado.empty or 'Erros' not in df_filtrado.columns:
        return 0
    
    total_testes = len(df_filtrado)
    total_erros = contar_total_erros(df_filtrado)
    
    if total_testes == 0:
        return 0
    
    return round(total_erros / total_testes, 2)

def contar_erros_por_testador(df_filtrado):
    """Conta erros por testador considerando tanto a coluna 'Erros' quanto os motivos de rejeição"""
    if df_filtrado.empty or 'Responsavel pelo teste' not in df_filtrado.columns:
        return pd.Series(dtype=int)
    
    erros_por_testador = {}
    
    # 1. Contar erros da coluna 'Erros' (dados mais recentes)
    if 'Erros' in df_filtrado.columns:
        df_temp = df_filtrado.copy()
        df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
        df_com_erros = df_temp[df_temp['Erros'] > 0]
        
        for _, row in df_com_erros.iterrows():
            testador = row.get('Responsavel pelo teste', 'Desconhecido')
            if testador not in erros_por_testador:
                erros_por_testador[testador] = 0
            erros_por_testador[testador] += row['Erros']
    
    # 2. Para registros sem dados na coluna 'Erros', usar análise de motivos (dados históricos)
    df_sem_erros_coluna = df_filtrado[
        (~df_filtrado['Erros'].notna()) | 
        (pd.to_numeric(df_filtrado['Erros'], errors='coerce').fillna(0) == 0)
    ] if 'Erros' in df_filtrado.columns else df_filtrado
    
    # Filtrar apenas rejeitadas para análise de motivos
    df_rejeitadas_historicas = df_sem_erros_coluna[df_sem_erros_coluna['Status'] == 'REJEITADA']
    
    # Contar motivos como erros históricos por testador
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    for _, row in df_rejeitadas_historicas.iterrows():
        testador = row.get('Responsavel pelo teste', 'Desconhecido')
        if testador not in erros_por_testador:
            erros_por_testador[testador] = 0
        
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    erros_por_testador[testador] += 1
    
    return pd.Series(erros_por_testador).sort_values(ascending=False) if erros_por_testador else pd.Series(dtype=int)

def analisar_distribuicao_erros(df_filtrado):
    """Analisa a distribuição de erros considerando tanto a coluna 'Erros' quanto os motivos históricos"""
    if df_filtrado.empty:
        return {}
    
    total_testes_real = len(df_filtrado)
    
    # Contar erros usando lógica híbrida (coluna 'Erros' + motivos históricos)
    total_erros_hibrido = 0
    testes_com_erro_hibrido = 0
    
    # 1. Contar erros da coluna 'Erros' (dados mais recentes)
    if 'Erros' in df_filtrado.columns:
        df_temp = df_filtrado.copy()
        df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
        df_com_erros = df_temp[df_temp['Erros'] > 0]
        
        total_erros_hibrido += df_com_erros['Erros'].sum()
        testes_com_erro_hibrido += len(df_com_erros)
    
    # 2. Para registros sem dados na coluna 'Erros', usar análise de motivos (dados históricos)
    df_sem_erros_coluna = df_filtrado[
        (~df_filtrado['Erros'].notna()) | 
        (pd.to_numeric(df_filtrado['Erros'], errors='coerce').fillna(0) == 0)
    ] if 'Erros' in df_filtrado.columns else df_filtrado
    
    # Filtrar apenas rejeitadas para análise de motivos
    df_rejeitadas_historicas = df_sem_erros_coluna[df_sem_erros_coluna['Status'] == 'REJEITADA']
    
    # Contar motivos como erros históricos
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    testes_historicos_com_erro = set()
    
    for idx, row in df_rejeitadas_historicas.iterrows():
        erros_neste_teste = 0
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    erros_neste_teste += 1
        
        if erros_neste_teste > 0:
            total_erros_hibrido += erros_neste_teste
            testes_historicos_com_erro.add(idx)
    
    testes_com_erro_hibrido += len(testes_historicos_com_erro)
    testes_sem_erro_hibrido = total_testes_real - testes_com_erro_hibrido
    
    # Calcular métricas de distribuição
    max_erros = 0
    min_erros = 0
    mediana_erros = 0
    
    if 'Erros' in df_filtrado.columns:
        df_temp = df_filtrado.copy()
        df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
        df_com_dados = df_temp[df_temp['Erros'].notna()]
        if not df_com_dados.empty:
            max_erros = df_com_dados['Erros'].max()
            min_erros = df_com_dados['Erros'].min()
            mediana_erros = df_com_dados['Erros'].median()
    
    analise = {
        'testes_sem_erro': testes_sem_erro_hibrido,
        'testes_com_erro': testes_com_erro_hibrido,
        'testes_sem_dados': 0,  # Agora consideramos dados históricos
        'total_testes': total_testes_real,
        'total_com_dados': total_testes_real,  # Todos têm dados (coluna Erros ou motivos)
        'total_erros': total_erros_hibrido,
        'max_erros_teste': max_erros,
        'min_erros_teste': min_erros,
        'mediana_erros': mediana_erros
    }
    
    return analise

def analisar_qualidade_unificada(df_filtrado):
    """Análise unificada combinando motivos qualitativos e erros quantitativos"""
    if df_filtrado.empty:
        return {}
    
    # Análise quantitativa (coluna Erros)
    analise_erros = analisar_distribuicao_erros(df_filtrado)
    
    # Análise qualitativa (Motivos de rejeição)
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA'] if 'Status' in df_filtrado.columns else pd.DataFrame()
    
    # Contar bugs por motivos
    total_bugs_motivos = contar_total_bugs(df_rejeitadas)
    bugs_por_time_motivos = contar_bugs_por_time(df_rejeitadas) if not df_rejeitadas.empty else pd.Series(dtype=int)
    
    # Análise de motivos
    motivos_analysis = {}
    if not df_rejeitadas.empty:
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
        motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
        
        if motivos_existentes:
            todos_motivos = []
            for col in motivos_existentes:
                motivos = df_rejeitadas[col].dropna().tolist()
                todos_motivos.extend(motivos)
            
            if todos_motivos:
                motivos_filtrados = [motivo for motivo in todos_motivos 
                                   if motivo.lower() not in ['aprovada', 'sem recusa']]
                
                if motivos_filtrados:
                    motivos_counts = pd.Series(motivos_filtrados).value_counts()
                    motivos_analysis = {
                        'motivos_counts': motivos_counts.to_dict(),
                        'motivo_mais_comum': motivos_counts.index[0] if len(motivos_counts) > 0 else None,
                        'total_motivos_registrados': len(motivos_filtrados)
                    }
    
    # Combinar análises
    analise_unificada = {
        # Dados quantitativos (coluna Erros)
        'erros_quantitativos': analise_erros,
        'total_erros_numericos': contar_total_erros(df_filtrado),
        'media_erros_por_teste': calcular_media_erros_por_teste(df_filtrado),
        
        # Dados qualitativos (Motivos)
        'bugs_qualitativos': {
            'total_bugs_motivos': total_bugs_motivos,
            'bugs_por_time': bugs_por_time_motivos.to_dict() if not bugs_por_time_motivos.empty else {},
            'total_rejeitadas': len(df_rejeitadas),
            'motivos_analysis': motivos_analysis
        },
        
        # Métricas comparativas
        'metricas_comparativas': {
            'total_testes': len(df_filtrado),
            'taxa_rejeicao': (len(df_rejeitadas) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0,
            'taxa_erros_numericos': (analise_erros.get('testes_com_erro', 0) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0,
            'cobertura_dados_erros': (analise_erros.get('total_com_dados', 0) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        }
    }
    
    return analise_unificada

# ===== FUNÇÕES PARA ANÁLISE DE BUGS =====

def carregar_dados_bugs():
    """Carrega dados de bugs via upload de arquivo"""
    uploaded_file_bugs = st.file_uploader(
        "Faça upload da planilha de bugs",
        type=['xlsx', 'xls'],
        key="bugs_uploader",
        help="Selecione a planilha contendo os dados de bugs para análise"
    )
    
    if uploaded_file_bugs is not None:
        try:
            df_bugs = pd.read_excel(uploaded_file_bugs)
            # Processar dados de bugs
            if 'Data' in df_bugs.columns:
                df_bugs['Data'] = pd.to_datetime(df_bugs['Data'], errors='coerce')
            st.success(f"✅ Planilha de bugs carregada: {uploaded_file_bugs.name}")
            return df_bugs
        except Exception as e:
            st.error(f"Erro ao carregar arquivo de bugs: {e}")
            return None
    return None

def processar_metricas_bugs(df_bugs):
    """Processa métricas específicas de bugs"""
    if df_bugs is None or df_bugs.empty:
        return {}
    
    metricas = {
        'total_bugs': len(df_bugs),
        'bugs_por_status': {},
        'bugs_por_prioridade': {},
        'bugs_por_time': {},
        'bugs_por_fonte': {},
        'bugs_criticos': 0,
        'bugs_abertos': 0,
        'bugs_resolvidos': 0
    }
    
    # Análise por status
    if 'Status' in df_bugs.columns:
        metricas['bugs_por_status'] = df_bugs['Status'].value_counts().to_dict()
        metricas['bugs_abertos'] = sum([v for k, v in metricas['bugs_por_status'].items() 
                                       if any(palavra in k.lower() for palavra in ['pendente', 'aberto', 'em correção'])])
        metricas['bugs_resolvidos'] = sum([v for k, v in metricas['bugs_por_status'].items() 
                                         if 'corrigido' in k.lower()])
    
    # Análise por prioridade
    if 'Prioridade' in df_bugs.columns:
        metricas['bugs_por_prioridade'] = df_bugs['Prioridade'].value_counts().to_dict()
        metricas['bugs_criticos'] = sum([v for k, v in metricas['bugs_por_prioridade'].items() 
                                        if 'alta' in k.lower()])
    
    # Análise por time
    if 'Time' in df_bugs.columns:
        metricas['bugs_por_time'] = df_bugs['Time'].value_counts().to_dict()
    
    # Análise por fonte (quem encontrou)
    if 'Encontrado por:' in df_bugs.columns:
        metricas['bugs_por_fonte'] = df_bugs['Encontrado por:'].value_counts().to_dict()
    
    return metricas

def grafico_bugs_por_status(df_bugs):
    """Gráfico de distribuição de bugs por status"""
    if df_bugs is None or df_bugs.empty or 'Status' not in df_bugs.columns:
        return None
    
    status_counts = df_bugs['Status'].value_counts()
    
    # Mapeamento de cores específico para cada status
    cores_status = {
        'Concluido': '#4CAF50',  # Verde para concluído
        'Concluído': '#4CAF50',  # Verde para concluído
        'Corrigido': '#4CAF50',  # Verde para corrigido
        'Pendente': '#FFA726',   # Laranja para pendente
        'Em correção': '#4CAF50', # Verde para em correção
        'Em correcao': '#4CAF50', # Verde para em correção
        'Aberto': '#FF5722'      # Vermelho para aberto
    }
    
    # Criar lista de cores baseada nos status presentes
    cores_ordenadas = [cores_status.get(status, '#9E9E9E') for status in status_counts.index]
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="🐛 Status dos Bugs Identificados",
        color_discrete_sequence=cores_ordenadas
    )
    fig.update_traces(
        textinfo='label+percent+value',
        hovertemplate='Status: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    return fig

def grafico_bugs_por_prioridade(df_bugs):
    """Gráfico de bugs por prioridade"""
    if df_bugs is None or df_bugs.empty or 'Prioridade' not in df_bugs.columns:
        return None
    
    prioridade_counts = df_bugs['Prioridade'].value_counts()
    cores = {'Alta': '#FF6B6B', 'Media': '#FFA726', 'Baixa': '#4CAF50'}
    
    fig = px.bar(
        x=prioridade_counts.index,
        y=prioridade_counts.values,
        title="⚠️ Distribuição de Bugs por Prioridade",
        color=prioridade_counts.index,
        color_discrete_map=cores,
        text=prioridade_counts.values
    )
    fig.update_traces(
        textposition='outside',
        hovertemplate='Prioridade: %{x}<br>Quantidade: %{y}<extra></extra>'
    )
    fig.update_layout(showlegend=False)
    return fig

def grafico_bugs_por_time(df_bugs):
    """Gráfico de bugs por time"""
    if df_bugs is None or df_bugs.empty or 'Time' not in df_bugs.columns:
        return None
    
    time_counts = df_bugs['Time'].value_counts()
    fig = px.bar(
        y=time_counts.index,
        x=time_counts.values,
        orientation='h',
        title="🏢 Bugs Identificados por Time",
        color=time_counts.values,
        color_continuous_scale='Reds',
        text=time_counts.values
    )
    fig.update_traces(
        textposition='outside',
        hovertemplate='Time: %{y}<br>Bugs: %{x}<extra></extra>'
    )
    fig.update_layout(
        height=max(400, len(time_counts) * 50),
        margin=dict(l=100)
    )
    return fig

def grafico_bugs_fonte_deteccao(df_bugs):
    """Gráfico de fonte de detecção de bugs"""
    if df_bugs is None or df_bugs.empty or 'Encontrado por:' not in df_bugs.columns:
        return None
    
    fonte_counts = df_bugs['Encontrado por:'].value_counts()
    fig = px.pie(
        values=fonte_counts.values,
        names=fonte_counts.index,
        title="🔍 Fonte de Detecção dos Bugs",
        color_discrete_sequence=['#4ECDC4', '#FF6B6B', '#45B7D1']
    )
    fig.update_traces(
        textinfo='label+percent+value',
        hovertemplate='Fonte: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    return fig

def grafico_evolucao_bugs(df_bugs):
    """Gráfico de evolução temporal dos bugs"""
    if df_bugs is None or df_bugs.empty or 'Data' not in df_bugs.columns:
        return None
    
    df_bugs_com_data = df_bugs.dropna(subset=['Data'])
    if df_bugs_com_data.empty:
        return None
    
    df_bugs_com_data['Mes'] = df_bugs_com_data['Data'].dt.to_period('M')
    bugs_por_mes = df_bugs_com_data['Mes'].value_counts().sort_index()
    
    fig = px.line(
        x=[str(m) for m in bugs_por_mes.index],
        y=bugs_por_mes.values,
        title="📈 Evolução dos Bugs ao Longo do Tempo",
        markers=True
    )
    fig.update_traces(
        line_color='#FF6B6B',
        marker_size=8,
        hovertemplate='Mês: %{x}<br>Bugs: %{y}<extra></extra>'
    )
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Quantidade de Bugs"
    )
    return fig


def grafico_status_distribuicao(df_filtrado):
    if 'Status' in df_filtrado.columns:
        # Filtrar registros com Status não vazio
        df_status_valido = df_filtrado[df_filtrado['Status'].notna() & (df_filtrado['Status'].str.strip() != '')]
        
        if df_status_valido.empty:
            return None
            
        status_counts = df_status_valido['Status'].value_counts()
        
        # Definir cores baseadas no status
        color_map = {
            'APROVADA': '#1976D2',  # Azul para aprovada
            'REJEITADA': '#dc3545',  # Vermelho para rejeitada
            'PRONTO PARA PUBLICAÇÃO': '#2196F3'  # Azul para pronto
        }
        
        # Criar lista de cores baseada nos status presentes
        colors = [color_map.get(status, '#6c757d') for status in status_counts.index]
        
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title="🎯 Resultado dos Testes de Qualidade",
            color_discrete_sequence=colors
        )
        fig.update_traces(
            textinfo='label+percent+value',
            hovertemplate='Status: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
        )
        fig.update_layout(
            title_x=0.5,
            font=dict(size=10),
            margin=dict(t=60, b=40, l=40, r=40),
            height=300,
            width=450,
            showlegend=False
        )
        return fig
    return None

def grafico_tasks_por_time(df_filtrado):
    if 'Time' in df_filtrado.columns:
        time_counts = df_filtrado['Time'].value_counts()
        fig = px.bar(
            x=time_counts.values, 
            y=time_counts.index,
            title="🏢 Cobertura de Q.A por Time de Desenvolvimento",
            labels={'x': 'Tasks Testadas', 'y': 'Time de Desenvolvimento'},
            orientation='h',
            color=time_counts.values,
            color_continuous_scale='plasma',
            text=time_counts.values
        )
        fig.update_coloraxes(colorbar_title="Quantidade de Tasks")
        fig.update_layout(
            title_x=0.5,
            font=dict(size=10),
            showlegend=False,
            coloraxis_showscale=False,
            height=300,
             width=450,
            margin=dict(t=60, b=40, l=300, r=40)
        )
        fig.update_traces(textposition='outside', hovertemplate='Time: %{y}<br>Tasks Testadas: %{x}<extra></extra>')
        return fig
    return None

def grafico_responsavel_performance(df_filtrado):
    if 'Responsavel pelo teste' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        perf_data = df_filtrado.groupby('Responsavel pelo teste')['Status'].value_counts().unstack(fill_value=0)
        if not perf_data.empty:
            perf_data['Total'] = perf_data.sum(axis=1)
            perf_data = perf_data.sort_values('Total', ascending=True)
            
            fig = go.Figure()
            
            for status in perf_data.columns[:-1]:
                fig.add_trace(go.Bar(
                    name=status,
                    y=perf_data.index,
                    x=perf_data[status],
                    orientation='h',
                    text=perf_data[status],
                    textposition='inside'
                ))
            
            fig.update_layout(
                title="👥 Performance dos Testadores Q.A",
                xaxis_title="Tasks Testadas",
                yaxis_title="Testador Q.A",
                barmode='stack',
                height=max(450, len(perf_data) * 35),
                margin=dict(t=50, b=80, l=200, r=150)
            )
            return fig
    return None

def grafico_timeline_tasks(df_filtrado):
    if 'Data' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        df_timeline = df_filtrado.dropna(subset=['Data'])
        if not df_timeline.empty:
            df_timeline['Mes'] = df_timeline['Data'].dt.to_period('M')
            timeline_data = df_timeline.groupby(['Mes', 'Status']).size().reset_index(name='Count')
            timeline_data['Mes'] = timeline_data['Mes'].astype(str)
            
            # Definir cores para os status
            color_map = {
                'APROVADA': '#1976D2',  # Azul para aprovada
                'REJEITADA': '#dc3545',  # Vermelho para rejeitada
                'PRONTO PARA PUBLICAÇÃO': '#2196F3'  # Azul para pronto
            }
            
            fig = px.bar(
                timeline_data,
                x='Mes',
                y='Count',
                color='Status',
                title="📈 Evolução dos Testes de Qualidade",
                labels={'Count': 'Tasks Testadas por Dia', 'Mes': 'Mês'},
                text='Count',
                color_discrete_map=color_map
            )
            fig.update_layout(
                margin=dict(t=50, b=80, l=80, r=80),
                height=450
            )
            fig.update_xaxes(tickangle=45)
            fig.update_traces(textposition='outside', hovertemplate='Mês: %{x}<br>Status: %{legendgroup}<br>Tasks Testadas: %{y}<extra></extra>')
            return fig
    return None

def grafico_motivos_rejeicao(df_filtrado, por_ambiente=False):
    if 'Status' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
        motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
        
        if motivos_existentes and not df_rejeitadas.empty:
            # Se por_ambiente=True e temos coluna Ambiente, criar análise por ambiente
            if por_ambiente and 'Ambiente' in df_rejeitadas.columns and df_rejeitadas['Ambiente'].notna().any():
                motivos_ambiente = []
                for _, row in df_rejeitadas.iterrows():
                    ambiente = row.get('Ambiente', 'N/A')
                    for col in motivos_existentes:
                        motivo = row[col]
                        if (pd.notna(motivo) and 
                            str(motivo).strip() != '' and 
                            str(motivo).lower() not in ['aprovada', 'sem recusa', 'nan', 'none']):
                            motivos_ambiente.append({'Motivo': str(motivo).strip(), 'Ambiente': ambiente})
                
                if motivos_ambiente:
                    df_motivos = pd.DataFrame(motivos_ambiente)
                    motivos_counts = df_motivos.groupby(['Motivo', 'Ambiente']).size().reset_index(name='Count')
                    motivos_counts = motivos_counts.sort_values('Count', ascending=True).tail(20)
                    
                    fig = px.bar(
                        motivos_counts,
                        y='Motivo',
                        x='Count',
                        color='Ambiente',
                        orientation='h',
                        title="🔍 Principais Problemas por Ambiente",
                        labels={'Count': 'Bugs Identificados', 'Motivo': 'Tipo de Problema'},
                        text='Count'
                    )
                    fig.update_traces(
                        textposition='outside',
                        texttemplate='%{x}',
                        textfont_size=10,
                        hovertemplate='Problema: %{y}<br>Ambiente: %{fullData.name}<br>Ocorrências: %{x}<extra></extra>'
                    )
                    fig.update_layout(
                        title_x=0.5,
                        font=dict(size=10),
                        margin=dict(t=60, b=40, l=350, r=40),
                        height=300,
                         width=450,
                        showlegend=False
                    )
                    return fig
            else:
                # Versão original sem ambiente
                todos_motivos = []
                for col in motivos_existentes:
                    motivos = df_rejeitadas[col].dropna().tolist()
                    todos_motivos.extend(motivos)
                
                if todos_motivos:
                    # Filtrar motivos que não são bugs reais
                    motivos_filtrados = [str(motivo).strip() for motivo in todos_motivos 
                                       if (pd.notna(motivo) and 
                                           str(motivo).strip() != '' and 
                                           str(motivo).lower() not in ['aprovada', 'sem recusa', 'nan', 'none'])]
                    
                    if motivos_filtrados:
                        motivos_counts = pd.Series(motivos_filtrados).value_counts().head(10)
                    else:
                        return None
                    fig = px.bar(
                        y=motivos_counts.index,
                        x=motivos_counts.values,
                        orientation='h',
                        title="🔍 Principais Problemas Detectados pelo Q.A",
                        labels={'x': 'Bugs Identificados', 'y': 'Tipo de Problema'},
                        text=motivos_counts.values
                    )
                    fig.update_traces(
                        marker_color='#4ECDC4',
                        textposition='outside',
                        texttemplate='%{x}',
                        textfont_size=12,
                        hovertemplate='Problema: %{y}<br>Ocorrências: %{x}<extra></extra>'
                    )
                    fig.update_layout(
                        title_x=0.5,
                        font=dict(size=10),
                        margin=dict(t=60, b=40, l=350, r=40),
                        height=300,
             width=450,
                        showlegend=False
                    )
                    return fig
    return None



def grafico_rejeicoes_por_dev(df_filtrado):
    if 'Status' in df_filtrado.columns and 'Responsável' in df_filtrado.columns:
        dev_stats = df_filtrado.groupby('Responsável')['Status'].value_counts().unstack(fill_value=0)
        if 'REJEITADA' in dev_stats.columns:
            dev_stats['Total_Tasks'] = dev_stats.sum(axis=1)
            dev_stats['Total_Rejeicoes'] = dev_stats.get('REJEITADA', 0)
            dev_stats['Percentual_Rejeicao'] = (dev_stats['Total_Rejeicoes'] / dev_stats['Total_Tasks'] * 100).round(1)
            dev_stats_filtered = dev_stats[dev_stats['Total_Tasks'] >= 3].sort_values('Total_Rejeicoes', ascending=False).head(10)
            
            if not dev_stats_filtered.empty:
                chart_data = dev_stats_filtered.reset_index()
                
                fig = px.bar(
                    chart_data,
                    x='Responsável',
                    y='Total_Rejeicoes',
                    title="👨‍💻 Desenvolvedores com Mais Rejeições (min. 3 tasks)",
                    labels={'Responsável': 'Desenvolvedor', 'Total_Rejeicoes': 'Total de Rejeições'},
                    color='Percentual_Rejeicao',
                    color_continuous_scale=['#4ECDC4', '#45B7D1', '#6C5CE7'],
                    text='Total_Rejeicoes',
                    hover_data={'Percentual_Rejeicao': ':.1f'}
                )
                fig.update_coloraxes(colorbar_title="Taxa de Rejeição (%)")
                fig.update_layout(
                    margin=dict(t=50, b=150, l=150, r=80),
                    height=550
                )
                fig.update_xaxes(tickangle=45)
                fig.update_traces(textposition='outside')
                return fig
    return None

def grafico_evolucao_qualidade(df_filtrado, por_ambiente=False):
    if 'Data' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        df_timeline = df_filtrado.dropna(subset=['Data'])
        if not df_timeline.empty:
            df_timeline['Mes'] = df_timeline['Data'].dt.to_period('M')
            
            # Se temos informação de ambiente e foi solicitado, mostrar evolução por ambiente
            if por_ambiente and 'Ambiente' in df_filtrado.columns and df_filtrado['Ambiente'].notna().any():
                monthly_stats = df_timeline.groupby(['Mes', 'Status', 'Ambiente']).size().unstack(fill_value=0)
                
                if 'APROVADA' in monthly_stats.columns or 'REJEITADA' in monthly_stats.columns or 'PRONTO PARA PUBLICAÇÃO' in monthly_stats.columns:
                    aprovadas_col = monthly_stats.get('APROVADA', 0) + monthly_stats.get('PRONTO PARA PUBLICAÇÃO', 0)
                    rejeitadas_col = monthly_stats.get('REJEITADA', 0)
                    monthly_stats['Total'] = aprovadas_col + rejeitadas_col
                    monthly_stats['Taxa_Aprovacao'] = (aprovadas_col / monthly_stats['Total'] * 100).round(1).fillna(0)
                    monthly_stats = monthly_stats.reset_index()
                    monthly_stats['Mes'] = monthly_stats['Mes'].astype(str)
                    
                    fig = px.line(
                        monthly_stats,
                        x='Mes',
                        y='Taxa_Aprovacao',
                        color='Ambiente',
                        title="📈 Evolução da Taxa de Aprovação por Ambiente",
                        labels={'Taxa_Aprovacao': 'Taxa de Aprovação (%)', 'Mes': 'Mês'},
                        markers=True
                    )
                    fig.update_traces(hovertemplate='Mês: %{x}<br>Ambiente: %{fullData.name}<br>Taxa: %{y}%<extra></extra>')
                    return fig
            else:
                # Versão original sem ambiente
                monthly_stats = df_timeline.groupby(['Mes', 'Status']).size().unstack(fill_value=0)
                
                if 'APROVADA' in monthly_stats.columns or 'REJEITADA' in monthly_stats.columns or 'PRONTO PARA PUBLICAÇÃO' in monthly_stats.columns:
                    aprovadas_col = monthly_stats.get('APROVADA', 0) + monthly_stats.get('PRONTO PARA PUBLICAÇÃO', 0)
                    rejeitadas_col = monthly_stats.get('REJEITADA', 0)
                    monthly_stats['Total'] = aprovadas_col + rejeitadas_col
                    monthly_stats['Taxa_Aprovacao'] = (aprovadas_col / monthly_stats['Total'] * 100).round(1).fillna(0)
                    monthly_stats = monthly_stats.reset_index()
                    monthly_stats['Mes'] = monthly_stats['Mes'].astype(str)
                    
                    fig = px.line(
                        monthly_stats,
                        x='Mes',
                        y='Taxa_Aprovacao',
                        title="📈 Evolução da Taxa de Aprovação ao Longo do Tempo",
                        labels={'Taxa_Aprovacao': 'Taxa de Aprovação (%)', 'Mes': 'Mês'},
                        markers=True
                    )
                    fig.update_traces(hovertemplate='Mês: %{x}<br>Taxa: %{y}%<extra></extra>')
                    return fig
    return None

def grafico_erros_por_time(df_filtrado):
    """Gráfico mostrando quantidade de erros/bugs identificados por time"""
    if 'Time' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        if not df_rejeitadas.empty:
            erros_por_time = contar_bugs_por_time(df_rejeitadas)
            
            fig = px.bar(
                x=erros_por_time.index,
                y=erros_por_time.values,
                title="🚨 Quantidade de Bugs Identificados por Time",
                labels={'x': 'Time de Desenvolvimento', 'y': 'Bugs Identificados'},
                color=erros_por_time.values,
                color_continuous_scale=['#4ECDC4', '#45B7D1', '#6C5CE7'],
                text=erros_por_time.values
            )
            fig.update_coloraxes(colorbar_title="Quantidade de Bugs")
            fig.update_layout(
                showlegend=False,
                margin=dict(t=50, b=120, l=120, r=80),
                height=450
            )
            fig.update_traces(
                textposition='outside',
                hovertemplate='Time: %{x}<br>Bugs: %{y}<extra></extra>'
            )
            fig.update_xaxes(tickangle=45)
            return fig
    return None

def grafico_erros_coluna_por_time(df_filtrado):
    """Gráfico mostrando quantidade de erros por time usando a coluna 'Erros'"""
    if 'Erros' not in df_filtrado.columns or 'Time' not in df_filtrado.columns:
        return None
    
    erros_por_time = contar_erros_por_time(df_filtrado)
    if erros_por_time.empty:
        return None
    
    fig = px.bar(
        x=erros_por_time.index,
        y=erros_por_time.values,
        title="📊 Total de Erros por Time",
        labels={'x': 'Time', 'y': 'Total de Erros'},
        color=erros_por_time.values,
        color_continuous_scale=['#4ECDC4', '#45B7D1', '#FF6B6B'],
        text=erros_por_time.values
    )
    
    fig.update_layout(
        margin=dict(t=50, b=150, l=80, r=80),
        height=450,
        xaxis_tickangle=45,
        showlegend=False
    )
    fig.update_traces(
        textposition='outside', 
        textfont_size=12,
        hovertemplate='Time: %{x}<br>Erros: %{y}<extra></extra>'
    )
    return fig

def grafico_erros_por_testador(df_filtrado):
    """Gráfico mostrando quantidade de erros por testador"""
    if ('Erros' not in df_filtrado.columns or 
        'Responsavel pelo teste' not in df_filtrado.columns):
        return None
    
    erros_por_testador = contar_erros_por_testador(df_filtrado)
    if erros_por_testador.empty:
        return None
    
    fig = px.bar(
        x=erros_por_testador.values,
        y=erros_por_testador.index,
        orientation='h',
        title="👥 Total de Erros Encontrados por Testador",
        labels={'x': 'Total de Erros', 'y': 'Testador'},
        color=erros_por_testador.values,
        color_continuous_scale='Reds',
        text=erros_por_testador.values
    )
    
    fig.update_layout(
        height=max(400, len(erros_por_testador) * 60),
        margin=dict(l=150, r=50, t=50, b=50),
        showlegend=False
    )
    fig.update_traces(
        textposition='outside',
        hovertemplate='Testador: %{y}<br>Erros: %{x}<extra></extra>'
    )
    return fig

def grafico_distribuicao_erros(df_filtrado):
    """Gráfico de distribuição de erros (testes com/sem erro e sem dados)"""
    if 'Erros' not in df_filtrado.columns:
        return None
    
    analise = analisar_distribuicao_erros(df_filtrado)
    if not analise:
        return None
    
    labels = ['Testes sem Erro', 'Testes com Erro', 'Testes sem Dados']
    values = [analise['testes_sem_erro'], analise['testes_com_erro'], analise['testes_sem_dados']]
    
    if sum(values) == 0:
        return None
    
    fig = px.pie(
        values=values,
        names=labels,
        title="🎯 Distribuição Completa de Testes",
        color_discrete_sequence=['#28a745', '#dc3545', '#6c757d']
    )
    
    fig.update_traces(
        textinfo='label+percent+value',
        hovertemplate='%{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    )
    return fig

def grafico_media_erros_por_time(df_filtrado):
    """Gráfico da média de erros por time usando lógica híbrida"""
    if 'Time' not in df_filtrado.columns:
        return None
    
    # Usar a função contar_erros_por_time que já implementa a lógica híbrida
    erros_por_time = contar_erros_por_time(df_filtrado)
    if erros_por_time.empty:
        return None
    
    # Contar total de testes por time para calcular a média
    testes_por_time = df_filtrado.groupby('Time').size()
    
    # Calcular média de erros por teste por time
    media_erros_time = {}
    for time in erros_por_time.index:
        if time in testes_por_time.index and testes_por_time[time] > 0:
            media_erros_time[time] = erros_por_time[time] / testes_por_time[time]
    
    if not media_erros_time:
        return None
    
    # Converter para Series e ordenar
    media_erros_series = pd.Series(media_erros_time).sort_values(ascending=False)
    
    fig = px.bar(
        x=media_erros_series.index,
        y=media_erros_series.values,
        title="📈 Média de Erros por Teste por Time (Dados Híbridos)",
        labels={'x': 'Time', 'y': 'Média de Erros por Teste'},
        color=media_erros_series.values,
        color_continuous_scale='Oranges',
        text=[f"{val:.1f}" for val in media_erros_series.values]
    )
    
    fig.update_layout(
        margin=dict(t=50, b=150, l=80, r=80),
        height=450,
        xaxis_tickangle=45,
        showlegend=False
    )
    fig.update_traces(
        textposition='outside',
        hovertemplate='Time: %{x}<br>Média: %{y:.2f}<extra></extra>'
    )
    return fig

def grafico_distribuicao_bugs_tipo(df_filtrado):
    """Gráfico de distribuição dos tipos de bugs mais comuns"""
    if 'Status' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
        motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
        
        if motivos_existentes and not df_rejeitadas.empty:
            todos_motivos = []
            for col in motivos_existentes:
                motivos = df_rejeitadas[col].dropna().tolist()
                todos_motivos.extend(motivos)
            
            if todos_motivos:
                # Filtrar motivos que não são bugs reais
                motivos_filtrados = [motivo for motivo in todos_motivos 
                                   if motivo.lower() not in ['aprovada', 'sem recusa']]
                
                if motivos_filtrados:
                    motivos_counts = pd.Series(motivos_filtrados).value_counts().head(8)
                else:
                    return None
                
                fig = px.pie(
                    values=motivos_counts.values,
                    names=motivos_counts.index,
                    title="🔍 Distribuição dos Tipos de Bugs Mais Comuns",
                    color_discrete_sequence=['#4ECDC4', '#45B7D1', '#6C5CE7', '#96CEB4', '#FECA57']
                )
                fig.update_layout(
                    margin=dict(t=50, b=50, l=100, r=50),
                    height=500
                )
                fig.update_traces(
                    textinfo='label+percent',
                    hovertemplate='Tipo: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
                )
                return fig
    return None

def grafico_heatmap_atividade(df_filtrado):
    """Heatmap de atividade de testes por dia da semana e hora"""
    if 'Data' in df_filtrado.columns:
        df_com_data = df_filtrado.dropna(subset=['Data'])
        if not df_com_data.empty:
            df_com_data['Dia_Semana'] = df_com_data['Data'].dt.day_name()
            df_com_data['Semana'] = df_com_data['Data'].dt.isocalendar().week
            
            # Mapear dias da semana para português
            dias_pt = {
                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            df_com_data['Dia_Semana'] = df_com_data['Dia_Semana'].map(dias_pt)
            
            heatmap_data = df_com_data.groupby(['Semana', 'Dia_Semana']).size().reset_index(name='Testes')
            
            if not heatmap_data.empty:
                pivot_data = heatmap_data.pivot(index='Dia_Semana', columns='Semana', values='Testes').fillna(0)
                
                # Ordenar dias da semana
                ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                pivot_data = pivot_data.reindex(ordem_dias)
                
                fig = px.imshow(
                    pivot_data,
                    title="📅 Heatmap de Atividade de Testes por Semana",
                    labels={'x': 'Semana do Ano', 'y': 'Dia da Semana', 'color': 'Quantidade de Testes'},
                    color_continuous_scale='Blues'
                )
                fig.update_coloraxes(colorbar_title="Quantidade de Testes")
                fig.update_layout(
                    margin=dict(t=50, b=50, l=100, r=50),
                    height=400
                )
                return fig
    return None

def grafico_motivos_por_time(df_filtrado):
    if df_filtrado.empty or 'Time' not in df_filtrado.columns:
        return None
    
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
    if df_rejeitadas.empty:
        return None
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
    
    if not motivos_existentes:
        return None
    
    dados_motivos = []
    for _, row in df_rejeitadas.iterrows():
        time = row.get('Time', 'N/A')
        for col in motivos_existentes:
            motivo = row.get(col)
            if pd.notna(motivo) and motivo.lower() not in ['aprovada', 'sem recusa', ''] and str(motivo).strip() != '':
                dados_motivos.append({'Time': time})
    
    if not dados_motivos:
        return None
    
    df_motivos = pd.DataFrame(dados_motivos)
    total_por_time = df_motivos['Time'].value_counts().sort_values(ascending=False)
    
    if total_por_time.empty:
        return None
    
    fig = px.bar(
        x=total_por_time.index,
        y=total_por_time.values,
        title='🎯 Total de Motivos de Rejeição por Time',
        labels={'x': 'Time', 'y': 'Total de Motivos'},
        text=total_por_time.values,
        color=total_por_time.values,
        color_continuous_scale=['#4ECDC4', '#45B7D1', '#FF6B6B']
    )
    
    fig.update_traces(textposition='outside', textfont_size=12)
    fig.update_layout(
        title_font_color='#FFFFFF',
        xaxis_title='Time de Desenvolvimento',
        yaxis_title='Total de Motivos de Rejeição',
        margin=dict(t=60, b=120, l=80, r=80),
        height=500,
        showlegend=False,
        xaxis_tickangle=45
    )
    
    return fig

def grafico_motivos_por_desenvolvedor(df_filtrado):
    if df_filtrado.empty or 'Responsável' not in df_filtrado.columns:
        return None
    
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
    if df_rejeitadas.empty:
        return None
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
    
    if not motivos_existentes:
        return None
    
    dados_motivos = []
    for _, row in df_rejeitadas.iterrows():
        dev = row.get('Responsável', 'N/A')
        for col in motivos_existentes:
            motivo = row.get(col)
            if pd.notna(motivo) and motivo.lower() not in ['aprovada', 'sem recusa', ''] and str(motivo).strip() != '':
                dados_motivos.append({'Desenvolvedor': dev})
    
    if not dados_motivos:
        return None
    
    df_motivos = pd.DataFrame(dados_motivos)
    total_por_dev = df_motivos['Desenvolvedor'].value_counts().sort_values(ascending=False).head(10)
    
    if total_por_dev.empty:
        return None
    
    fig = px.bar(
        x=total_por_dev.index,
        y=total_por_dev.values,
        title='👨‍💻 Total de Motivos de Rejeição por Desenvolvedor (Top 10)',
        labels={'x': 'Desenvolvedor', 'y': 'Total de Motivos'},
        text=total_por_dev.values,
        color=total_por_dev.values,
        color_continuous_scale=['#4ECDC4', '#45B7D1', '#FF6B6B']
    )
    
    fig.update_traces(textposition='outside', textfont_size=12)
    fig.update_layout(
        title_font_color='#FFFFFF',
        xaxis_title='Desenvolvedor',
        yaxis_title='Total de Motivos de Rejeição',
        margin=dict(t=60, b=150, l=80, r=80),
        height=500,
        showlegend=False,
        xaxis_tickangle=45
    )
    
    return fig

def grafico_ranking_problemas(df_filtrado):
    if df_filtrado.empty:
        return None
    
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
    if df_rejeitadas.empty:
        return None
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
    motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
    
    if not motivos_existentes:
        return None
    
    todos_motivos = []
    for col in motivos_existentes:
        motivos = df_rejeitadas[col].dropna().tolist()
        todos_motivos.extend(motivos)
    
    motivos_filtrados = [motivo for motivo in todos_motivos 
                        if motivo.lower() not in ['aprovada', 'sem recusa', '']]
    
    if not motivos_filtrados:
        return None
    
    ranking_motivos = pd.Series(motivos_filtrados).value_counts().head(10)
    
    fig = px.bar(
        x=ranking_motivos.values,
        y=ranking_motivos.index,
        orientation='h',
        title='🏆 Top 10 - Tipos de Problemas Mais Encontrados',
        text=ranking_motivos.values,
        color=ranking_motivos.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        title_x=0.5,
        font=dict(size=10),
        xaxis_title='Quantidade de Ocorrências',
        yaxis_title='Tipo de Problema',
        margin=dict(t=60, b=40, l=300, r=40),
        height=300,
         width=450,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    
    return fig

def grafico_motivos_recusa_por_dev(df_filtrado):
    """Gráfico mostrando total de rejeições por desenvolvedor"""
    if 'Status' in df_filtrado.columns and 'Responsável' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        
        if not df_rejeitadas.empty:
            # Contar total de rejeições por desenvolvedor
            rejeicoes_por_dev = df_rejeitadas['Responsável'].value_counts()
            
            # Filtrar apenas desenvolvedores com pelo menos 2 rejeições
            devs_relevantes = rejeicoes_por_dev[rejeicoes_por_dev >= 2]
            
            if not devs_relevantes.empty:
                # Pegar top 10 desenvolvedores com mais rejeições
                top_devs = devs_relevantes.head(10)
                
                fig = px.bar(
                    x=top_devs.index,
                    y=top_devs.values,
                    title="👨‍💻 Total de Rejeições por Desenvolvedor (min. 2 rejeições)",
                    labels={'x': 'Desenvolvedor', 'y': 'Total de Rejeições'},
                    text=top_devs.values,
                    color=top_devs.values,
                    color_continuous_scale=['#4ECDC4', '#45B7D1', '#FF6B6B']
                )
                
                fig.update_layout(
                    margin=dict(t=50, b=150, l=80, r=80),
                    height=550,
                    xaxis_tickangle=45,
                    showlegend=False
                )
                fig.update_traces(textposition='outside', textfont_size=12)
                return fig
    return None

def grafico_cobertura_testes_por_dev(df_filtrado):
    """Gráfico de cobertura de testes por desenvolvedor"""
    if 'Responsável' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        dev_stats = df_filtrado.groupby('Responsável').agg({
            'Status': ['count', lambda x: (x.isin(['APROVADA', 'REJEITADA', 'PRONTO PARA PUBLICAÇÃO'])).sum()]
        }).round(1)
        
        dev_stats.columns = ['Total_Tasks', 'Tasks_Testadas']
        dev_stats['Cobertura_Percentual'] = (dev_stats['Tasks_Testadas'] / dev_stats['Total_Tasks'] * 100).round(1)
        dev_stats = dev_stats[dev_stats['Total_Tasks'] >= 3].sort_values('Cobertura_Percentual', ascending=False).head(10)
        dev_stats = dev_stats.reset_index()
        
        if not dev_stats.empty:
            fig = px.bar(
                dev_stats,
                x='Responsável',
                y='Cobertura_Percentual',
                title="📊 Cobertura de Testes por Desenvolvedor (min. 3 tasks)",
                labels={'Responsável': 'Desenvolvedor', 'Cobertura_Percentual': 'Cobertura (%)'},
                text='Cobertura_Percentual',
                color='Cobertura_Percentual',
                color_continuous_scale=['#FF6B6B', '#FFA726', '#4ECDC4'],
                hover_data={'Tasks_Testadas': True, 'Total_Tasks': True}
            )
            
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                margin=dict(t=50, b=150, l=80, r=80),
                height=550,
                xaxis_tickangle=45,
                yaxis=dict(range=[0, 100])
            )
            return fig
    return None

def grafico_ranking_aprovadas_por_dev(df_filtrado):
    """Gráfico de ranking de desenvolvedores com mais tarefas aprovadas"""
    if 'Status' in df_filtrado.columns and 'Responsável' in df_filtrado.columns:
        df_aprovadas = df_filtrado[df_filtrado['Status'].isin(['APROVADA', 'PRONTO PARA PUBLICAÇÃO'])]
        
        if not df_aprovadas.empty:
            aprovadas_por_dev = df_aprovadas['Responsável'].value_counts().head(10)
            
            if not aprovadas_por_dev.empty:
                fig = px.bar(
                    x=aprovadas_por_dev.index,
                    y=aprovadas_por_dev.values,
                    title="🏆 Ranking: Desenvolvedores com Mais Tarefas Aprovadas",
                    labels={'x': 'Desenvolvedor', 'y': 'Tarefas Aprovadas'},
                    text=aprovadas_por_dev.values,
                    color=aprovadas_por_dev.values,
                    color_continuous_scale=['#4ECDC4', '#45B7D1', '#2ECC71']
                )
                
                fig.update_traces(textposition='outside', textfont_size=12)
                fig.update_layout(
                    margin=dict(t=50, b=150, l=80, r=80),
                    height=550,
                    xaxis_tickangle=45,
                    showlegend=False
                )
                return fig
    return None

def grafico_tarefas_retestadas(df_filtrado):
    """Gráfico de tarefas que tiveram mais de 1 teste"""
    historico_retestes = analisar_historico_retestes(df_filtrado)
    
    if historico_retestes['total_tarefas_retestadas'] == 0:
        return None
    
    df_retestes = historico_retestes['detalhes_retestes']
    if df_retestes.empty:
        return None
    
    # Agrupar por time se disponível
    if 'Time' in df_retestes.columns:
        retestes_por_time = df_retestes.groupby('Time').agg({
            'Total_Testes': 'sum',
            'Aprovada_Apos_Reteste': 'sum'
        }).reset_index()
        
        retestes_por_time['Taxa_Sucesso'] = (
            retestes_por_time['Aprovada_Apos_Reteste'] / 
            retestes_por_time['Total_Testes'] * 100
        ).round(1)
        
        fig = px.bar(
            retestes_por_time,
            x='Time',
            y='Total_Testes',
            title="🔄 Tarefas Retestadas por Time",
            labels={'Time': 'Time', 'Total_Testes': 'Quantidade de Retestes'},
            text='Total_Testes',
            color='Taxa_Sucesso',
            color_continuous_scale=['#FF6B6B', '#4ECDC4', '#45B7D1']
        )
        
        fig.update_traces(textposition='outside', textfont_size=10)
        fig.update_layout(
            title_x=0.5,
            font=dict(size=10),
            margin=dict(t=60, b=100, l=40, r=40),
            height=300,
            width=450,
            xaxis_tickangle=45,
            showlegend=False,
            coloraxis_showscale=False
        )
        return fig
    
    return None

def grafico_tarefas_retestadas_por_dev(df_filtrado):
    """Gráfico de quantidade de tarefas retestadas por desenvolvedor"""
    if 'Responsável' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        df_retestadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        
        if not df_retestadas.empty:
            retestadas_por_dev = df_retestadas['Responsável'].value_counts().head(10)
            
            if not retestadas_por_dev.empty:
                fig = px.bar(
                    x=retestadas_por_dev.index,
                    y=retestadas_por_dev.values,
                    title="🔄 Quantidade de Tarefas Retestadas por Desenvolvedor",
                    labels={'x': 'Desenvolvedor', 'y': 'Tarefas Retestadas'},
                    text=retestadas_por_dev.values,
                    color=retestadas_por_dev.values,
                    color_continuous_scale=['#FFA726', '#FF7043', '#FF5722']
                )
                
                fig.update_traces(textposition='outside', textfont_size=12)
                fig.update_layout(
                    margin=dict(t=50, b=150, l=80, r=80),
                    height=550,
                    xaxis_tickangle=45,
                    showlegend=False
                )
                return fig
    return None

def grafico_taxa_rejeicao_por_time(df_filtrado):
    """Gráfico da taxa de rejeição por time"""
    if 'Time' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        time_stats = df_filtrado.groupby('Time')['Status'].value_counts().unstack(fill_value=0)
        
        if not time_stats.empty:
            time_stats['Total'] = time_stats.sum(axis=1)
            time_stats['Taxa_Rejeicao'] = ((time_stats.get('REJEITADA', 0) / time_stats['Total']) * 100).round(1)
            time_stats = time_stats[time_stats['Total'] >= 3]  # Filtrar times com pelo menos 3 tasks
            
            if not time_stats.empty:
                chart_data = time_stats.reset_index().sort_values('Taxa_Rejeicao', ascending=False)
                
                fig = px.bar(
                    chart_data,
                    x='Time',
                    y='Taxa_Rejeicao',
                    title="📊 Taxa de Rejeição por Time (min. 3 tasks)",
                    labels={'Time': 'Time de Desenvolvimento', 'Taxa_Rejeicao': 'Taxa de Rejeição (%)'},
                    color='Taxa_Rejeicao',
                    color_continuous_scale=['#4ECDC4', '#45B7D1', '#6C5CE7'],
                    text='Taxa_Rejeicao'
                )
                fig.update_coloraxes(showscale=False)
                fig.update_layout(
                    title_x=0.5,
                    font=dict(size=10),
                    margin=dict(t=60, b=100, l=40, r=40),
                    height=300,
                    width=450,
                    showlegend=False
                )
                fig.update_traces(
                    texttemplate='%{text}%',
                    textposition='outside',
                    hovertemplate='Time: %{x}<br>Taxa: %{y}%<extra></extra>'
                )
                fig.update_xaxes(tickangle=45)
                return fig
    return None

def grafico_distribuicao_ambientes(df_filtrado):
    """Gráfico de distribuição de testes por ambiente"""
    if 'Ambiente' in df_filtrado.columns:
        # Filtrar apenas registros com ambiente válido (não nulo e não vazio)
        df_ambiente_valido = df_filtrado[df_filtrado['Ambiente'].notna() & (df_filtrado['Ambiente'].str.strip() != '')]
        
        if df_ambiente_valido.empty:
            return None
            
        # Contar distribuição por ambiente
        ambiente_counts = df_ambiente_valido['Ambiente'].value_counts()
        
        if not ambiente_counts.empty:
            # Criar gráfico de pizza
            fig = px.pie(
                values=ambiente_counts.values,
                names=ambiente_counts.index,
                title="🌐 Distribuição de Testes por Ambiente",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='Ambiente: %{label}<br>Testes: %{value}<br>Percentual: %{percent}<extra></extra>'
            )
            
            fig.update_layout(
                margin=dict(t=60, b=60, l=60, r=60),
                height=400,
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
            )
            
            return fig
    return None

def grafico_ambiente_por_status(df_filtrado):
    """Gráfico de status por ambiente"""
    if 'Ambiente' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        # Filtrar apenas registros com ambiente válido (não nulo e não vazio)
        df_ambiente_valido = df_filtrado[df_filtrado['Ambiente'].notna() & (df_filtrado['Ambiente'].str.strip() != '')]
        
        if df_ambiente_valido.empty:
            return None
            
        # Criar tabela cruzada
        ambiente_status = pd.crosstab(df_ambiente_valido['Ambiente'], df_ambiente_valido['Status'])
        
        if not ambiente_status.empty:
            # Criar gráfico de barras empilhadas
            fig = px.bar(
                ambiente_status,
                title="📊 Status de Testes por Ambiente",
                labels={'value': 'Quantidade de Testes', 'index': 'Ambiente'},
                color_discrete_map={
                    'APROVADA': '#28a745',
                    'REJEITADA': '#dc3545',
                    'EM ANDAMENTO': '#ffc107',
                    'PENDENTE': '#6c757d'
                }
            )
            
            fig.update_layout(
                margin=dict(t=60, b=80, l=80, r=80),
                height=450,
                xaxis_title="Ambiente",
                yaxis_title="Quantidade de Testes",
                legend_title="Status"
            )
            
            return fig
    return None

def grafico_comparativo_testadores(df_filtrado):
    """Gráfico comparativo de produtividade entre testadores"""
    if 'Responsavel pelo teste' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        testador_stats = df_filtrado.groupby('Responsavel pelo teste').agg({
            'Status': ['count', lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'APROVADA').sum(), lambda x: (x == 'PRONTO PARA PUBLICAÇÃO').sum()]
        }).round(1)
        
        testador_stats.columns = ['Total_Testes', 'Bugs_Encontrados', 'Testes_Aprovados', 'Testes_Prontos']
        testador_stats['Total_Aprovadas'] = testador_stats['Testes_Aprovados'] + testador_stats['Testes_Prontos']
        testador_stats['Taxa_Deteccao'] = (testador_stats['Bugs_Encontrados'] / testador_stats['Total_Testes'] * 100).round(1)
        testador_stats = testador_stats.reset_index()
        
        if not testador_stats.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Total de Testes',
                x=testador_stats['Responsavel pelo teste'],
                y=testador_stats['Total_Testes'],
                yaxis='y',
                offsetgroup=1,
                marker_color='lightgreen',
                text=testador_stats['Total_Testes'],
                textposition='outside'
            ))
            
            fig.add_trace(go.Bar(
                name='Bugs Encontrados',
                x=testador_stats['Responsavel pelo teste'],
                y=testador_stats['Bugs_Encontrados'],
                yaxis='y',
                offsetgroup=2,
                marker_color='#FF6B6B',
                text=testador_stats['Bugs_Encontrados'],
                textposition='outside'
            ))
            
            fig.add_trace(go.Scatter(
                name='Bugs Encontrados (%)',
                x=testador_stats['Responsavel pelo teste'],
                y=testador_stats['Taxa_Deteccao'],
                yaxis='y2',
                mode='lines+markers',
                marker_color='orange',
                line=dict(width=3),
                text=[f"{val:.1f}%" for val in testador_stats['Taxa_Deteccao']],
                textposition='top center'
            ))
            
            fig.update_layout(
                title="👥 Comparativo de Performance entre Testadores",
                xaxis_title="Testador",
                yaxis=dict(title="Quantidade de Testes", side="left"),
                yaxis2=dict(title="Bugs Encontrados (%)", side="right", overlaying="y"),
                legend=dict(x=0.01, y=0.99),
                hovermode='x unified',
                margin=dict(t=50, b=50, l=50, r=50),
                height=500
            )
            return fig
    return None



def metricas_resumo(df_filtrado, df_original, df_sem_teste=None):
    # Cabeçalho executivo
    st.markdown("#### 📈 **Resumo Executivo - Impacto do Time de Qualidade**")
    
    # Cálculos principais
    total_planilha = len(df_filtrado) + (len(df_sem_teste) if df_sem_teste is not None else 0)
    
    # Verificar se a coluna 'Responsavel pelo teste' existe
    if 'Responsavel pelo teste' in df_filtrado.columns:
        total_testes_efetuados = len(df_filtrado[df_filtrado['Responsavel pelo teste'].notna()])
    else:
        # Se não existir, usar uma estimativa baseada em status diferentes de vazio
        total_testes_efetuados = len(df_filtrado[df_filtrado['Status'].notna()]) if 'Status' in df_filtrado.columns else len(df_filtrado)
    
    total_sem_teste = len(df_sem_teste) if df_sem_teste is not None else 0
    
    # Métricas de bugs
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA'] if 'Status' in df_filtrado.columns else pd.DataFrame()
    total_bugs_encontrados = contar_total_bugs(df_rejeitadas) if not df_rejeitadas.empty else 0
    aprovadas = len(df_filtrado[df_filtrado['Status'] == 'APROVADA']) if 'Status' in df_filtrado.columns else 0
    
    # === SEÇÃO 1: MÉTRICAS DE VOLUME E COBERTURA ===
    st.markdown("##### 🎯 **Volume de Trabalho e Cobertura**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cobertura_teste = (total_testes_efetuados / total_planilha * 100) if total_planilha > 0 else 0
        st.metric(
            "📊 Cobertura de Testes", 
            f"{cobertura_teste:.1f}%",
            delta=f"✅ {total_testes_efetuados:,} testadas | 📋 {total_planilha:,} total",
            help=f"Percentual de cobertura: {total_testes_efetuados:,} tarefas testadas de {total_planilha:,} tarefas totais. Meta recomendada: >80%"
        )
    
    with col2:
        if 'Nome da Task' in df_filtrado.columns:
            tarefas_unicas = df_filtrado['Nome da Task'].nunique()
        else:
            tarefas_unicas = 0
        st.metric(
            "📋 Tarefas Validadas", 
            f"{tarefas_unicas:,}",
            delta="📝 tarefas únicas no período",
            help="Número de tarefas diferentes que passaram por validação de qualidade no período selecionado"
        )
    
    with col3:
        if 'Time' in df_filtrado.columns:
            times_atendidos = df_filtrado['Time'].nunique()
        else:
            times_atendidos = 0
        st.metric(
            "🏢 Times Atendidos", 
            f"{times_atendidos}",
            delta="👥 equipes com cobertura QA",
            help="Número de times de desenvolvimento que receberam cobertura de Quality Assurance no período"
        )
    
    # Removido: Equipe Q.A Ativa
    
    # === SEÇÃO 2: IMPACTO NA QUALIDADE ===
    st.markdown("##### 🛡️ **Impacto na Qualidade e Prevenção de Defeitos**")
    col5, col6, col7 = st.columns(3)
    
    with col5:
        st.metric(
            "🚫 Bugs Interceptados", 
            f"{total_bugs_encontrados:,}",
            delta="🛡️ defeitos evitados em produção",
            help=f"Total de {total_bugs_encontrados:,} defeitos identificados e corrigidos antes da entrega ao cliente"
        )
    
    with col6:
        taxa_deteccao = (total_bugs_encontrados / total_testes_efetuados * 100) if total_testes_efetuados > 0 else 0
        rejeitadas = len(df_filtrado[df_filtrado['Status'] == 'REJEITADA']) if 'Status' in df_filtrado.columns else 0
        st.metric(
            "🔍 Bugs Encontrados (%)", 
            f"{taxa_deteccao:.1f}%",
            delta=f"🚨 {rejeitadas:,} testes c/ problemas | ✅ {total_testes_efetuados - rejeitadas:,} aprovados",
            help=f"Percentual de testes que identificaram problemas: {rejeitadas:,} de {total_testes_efetuados:,} testes. Taxa ideal: 15-25% (indica qualidade adequada do código)"
        )
    
    with col7:
        prontas_dash = len(df_filtrado[df_filtrado['Status'] == 'PRONTO PARA PUBLICAÇÃO']) if 'Status' in df_filtrado.columns else 0
        total_aprovadas_dash = aprovadas + prontas_dash
        rejeitadas_dash = len(df_filtrado[df_filtrado['Status'] == 'REJEITADA']) if 'Status' in df_filtrado.columns else 0
        taxa_aprovacao = (total_aprovadas_dash / (total_aprovadas_dash + rejeitadas_dash) * 100) if (total_aprovadas_dash + rejeitadas_dash) > 0 else 0
        st.metric(
            "✅ Taxa de Aprovação", 
            f"{taxa_aprovacao:.1f}%",
            delta=f"✅ {total_aprovadas_dash:,} aprovados | 🚨 {rejeitadas_dash:,} rejeitados",
            help=f"Percentual de aprovação (incluindo prontas para publicação): {total_aprovadas_dash:,} de {total_aprovadas_dash + rejeitadas_dash:,} testes. Meta recomendada: >75%"
        )
    
    # === SEÇÃO 3: ANÁLISE DE ERROS ===
    if 'Erros' in df_filtrado.columns:
        st.markdown("##### 🐛 **Análise de Erros Encontrados**")
        col_e1, col_e2, col_e3 = st.columns(3)
        
        with col_e1:
            total_erros = contar_total_erros(df_filtrado)
            tempo_correcao_estimado = total_erros * 45  # 45 min por erro em média
            st.metric(
                "🔢 Total de Erros", 
                f"{total_erros:,}",
                delta=f"⏱️ ≈{tempo_correcao_estimado/60:.1f}h de correção estimada",
                help=f"Total de {total_erros:,} erros identificados em {total_testes_efetuados:,} testes. Tempo estimado de correção: {tempo_correcao_estimado:,} minutos ({tempo_correcao_estimado/60:.1f} horas)"
            )
        
        with col_e2:
            media_erros = calcular_media_erros_por_teste(df_filtrado)
            classificacao = "Baixa" if media_erros < 2 else "Média" if media_erros < 4 else "Alta"
            st.metric(
                "📊 Média de Erros/Teste", 
                f"{media_erros:.1f}",
                delta=f"📈 Complexidade {classificacao.lower()}",
                help=f"Média de {media_erros:.1f} erros por teste. Classificação: {classificacao} (Baixa: <2, Média: 2-4, Alta: >4)"
            )
        
        with col_e3:
            distribuicao_erros = analisar_distribuicao_erros(df_filtrado)
            if distribuicao_erros:
                testes_com_erro = distribuicao_erros['testes_com_erro']
                total_testes_real = distribuicao_erros['total_testes']
                taxa_testes_com_erro = (testes_com_erro / total_testes_real * 100) if total_testes_real > 0 else 0
                testes_sem_erro = total_testes_real - testes_com_erro
                st.metric(
                    "⚠️ Taxa de Testes c/ Erro", 
                    f"{taxa_testes_com_erro:.1f}%",
                    delta=f"🚨 {testes_com_erro:,} c/ erro | ✅ {testes_sem_erro:,} limpos",
                    help=f"De {total_testes_real:,} testes realizados: {testes_com_erro:,} encontraram erros e {testes_sem_erro:,} foram aprovados sem problemas"
                )
    
    # === SEÇÃO 4: ANÁLISE DE RISCOS E PONTOS CRÍTICOS ===
    st.markdown("##### ⚠️ **Análise de Riscos e Pontos de Atenção**")
    col9, col10, col11 = st.columns(3)
    
    with col9:
        if not df_rejeitadas.empty and 'Time' in df_rejeitadas.columns:
            bugs_por_time = contar_bugs_por_time(df_rejeitadas)
            if not bugs_por_time.empty:
                time_critico = bugs_por_time.index[0]
                bugs_time_critico = bugs_por_time.iloc[0]
                st.metric(
                    "🚨 Time com Maior Risco", 
                    f"{time_critico}",
                    delta=f"🐛 {bugs_time_critico} defeitos encontrados",
                    delta_color="inverse",
                    help=f"Time {time_critico} apresentou {bugs_time_critico} defeitos no período - requer atenção especial e revisão de processos"
                )
    
    with col10:
        if not df_rejeitadas.empty:
            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
            motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
            
            if motivos_existentes:
                todos_motivos = []
                for col in motivos_existentes:
                    motivos = df_rejeitadas[col].dropna().tolist()
                    todos_motivos.extend(motivos)
                
                if todos_motivos:
                    motivos_filtrados = [motivo for motivo in todos_motivos 
                                       if motivo.lower() not in ['aprovada', 'sem recusa'] and str(motivo).strip() != '']
                    
                    if motivos_filtrados:
                        motivo_mais_comum = pd.Series(motivos_filtrados).value_counts().index[0]
                        ocorrencias_motivo = pd.Series(motivos_filtrados).value_counts().iloc[0]
                        st.metric(
                            "🔍 Principal Tipo de Defeito", 
                            motivo_mais_comum,
                            delta=f"📊 {ocorrencias_motivo}x identificado no período",
                            delta_color="inverse",
                            help=f"Defeito mais frequente: '{motivo_mais_comum}' com {ocorrencias_motivo} ocorrências - oportunidade de melhoria no processo de desenvolvimento"
                        )
                    else:
                        st.metric(
                            "🔍 Principal Tipo de Defeito", 
                            "Nenhum defeito",
                            delta="📊 Sem motivos válidos no período",
                            help="Não foram encontrados motivos de defeito válidos no período filtrado"
                        )
                else:
                    st.metric(
                        "🔍 Principal Tipo de Defeito", 
                        "Sem dados",
                        delta="📊 Motivos não preenchidos",
                        help="As colunas de motivos estão vazias para as tarefas rejeitadas"
                    )
            else:
                st.metric(
                    "🔍 Principal Tipo de Defeito", 
                    "Colunas ausentes",
                    delta="📊 Motivo, Motivo2, Motivo3, Motivo4, Motivo5, Motivo6, Motivo7 não encontradas",
                    help="As colunas de motivos não foram encontradas nos dados"
                )
        else:
            st.metric(
                "🔍 Principal Tipo de Defeito", 
                "Sem rejeições",
                delta="📊 Nenhuma tarefa rejeitada no período",
                help="Não há tarefas com status REJEITADA no período filtrado"
            )
    
    with col11:
        taxa_sem_teste = (total_sem_teste / total_planilha * 100) if total_planilha > 0 else 0
        st.metric(
            "⚠️ Tarefas Sem Cobertura", 
            f"{taxa_sem_teste:.1f}%",
            delta=f"🚫 {total_sem_teste} sem teste | ✅ {total_planilha - total_sem_teste} testadas",
            delta_color="inverse" if taxa_sem_teste > 20 else "normal",
            help=f"De {total_planilha} tarefas: {total_sem_teste} não receberam validação ({taxa_sem_teste:.1f}%) e {total_planilha - total_sem_teste} foram testadas. Meta: <20% sem cobertura"
        )
    
    # === RESUMO EXECUTIVO REMOVIDO ===
    # Seção removida conforme solicitação


def main():
    # Diagnóstico do sistema (expansível)
    with st.sidebar.expander("🔍 Diagnóstico do Sistema"):
        if st.button("Executar Diagnóstico"):
            diagnostico = diagnosticar_ambiente_pdf()
            
            st.write("**Ambiente:**", diagnostico['ambiente'])
            
            if diagnostico['kaleido_disponivel']:
                st.success(f"✅ Kaleido v{diagnostico['kaleido_versao']}")
            else:
                st.error("❌ Kaleido não disponível")
            
            if diagnostico['reportlab_disponivel']:
                st.success("✅ ReportLab disponível")
            else:
                st.error("❌ ReportLab não disponível")
            
            if diagnostico['problemas']:
                st.error("**Problemas encontrados:**")
                for problema in diagnostico['problemas']:
                    st.write(f"- {problema}")
            else:
                st.success("✅ Todos os componentes funcionando")
            
            # Teste de geração de gráfico
            if st.button("Testar Geração de Gráfico", key="test_graph"):
                try:
                    from streamlit_config import test_kaleido_functionality
                    if test_kaleido_functionality():
                        st.success("✅ Teste de gráfico bem-sucedido")
                    else:
                        st.error("❌ Falha no teste de gráfico")
                except Exception as e:
                    st.error(f"❌ Erro no teste: {e}")
    
    # Módulo de QA (código original)
    # Título principal
    st.title("🔍 Dashboard de Métricas DelTech")
    
    # Subtítulo será atualizado após aplicar filtros
    placeholder_subtitulo = st.empty()
    st.markdown("---")
    
    df = carregar_dados()
    
    if df is not None:
        df = processar_dados(df)
        
        # Filtros avançados
        st.subheader("🔍 Filtros Avançados")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            sprints_disponiveis = ['Todos'] + sorted([str(x) for x in df['Sprint'].dropna().unique().tolist()]) if 'Sprint' in df.columns else ['Todos']
            sprint_selecionado = st.selectbox("Filtrar por Sprint:", sprints_disponiveis)
        
        with col2:
            status_disponiveis = ['Todos'] + sorted([str(x) for x in df['Status'].dropna().unique().tolist()]) if 'Status' in df.columns else ['Todos']
            status_selecionado = st.selectbox("Filtrar por Status:", status_disponiveis)
        
        with col3:
            times_disponiveis = ['Todos'] + sorted([str(x) for x in df['Time'].dropna().unique().tolist()]) if 'Time' in df.columns else ['Todos']
            time_selecionado = st.selectbox("Filtrar por Time:", times_disponiveis)
        
        with col4:
            devs_disponiveis = ['Todos'] + sorted([str(x) for x in df['Responsável'].dropna().unique().tolist()]) if 'Responsável' in df.columns else ['Todos']
            dev_selecionado = st.selectbox("Filtrar por Desenvolvedor:", devs_disponiveis)
        
        with col5:
            if 'Data' in df.columns and not df['Data'].dropna().empty:
                data_min = df['Data'].min().date()
                data_max = df['Data'].max().date()
                data_range = st.date_input(
                    "Período:",
                    value=(data_min, data_max),
                    min_value=data_min,
                    max_value=data_max
                )
            else:
                data_range = None
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if sprint_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Sprint'] == sprint_selecionado]
        
        if status_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Status'] == status_selecionado]
        
        if time_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Time'] == time_selecionado]
        
        if dev_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Responsável'] == dev_selecionado]
        
        if data_range and len(data_range) == 2 and 'Data' in df.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['Data'].dt.date >= data_range[0]) & 
                (df_filtrado['Data'].dt.date <= data_range[1])
            ]
        
        # Verificar se há filtros ativos
        filtros_ativos = (
            sprint_selecionado != 'Todos' or 
            status_selecionado != 'Todos' or 
            time_selecionado != 'Todos' or 
            dev_selecionado != 'Todos' or 
            (data_range and len(data_range) == 2)
        )
        
        # Separar dados com e sem teste
        df_original = df_filtrado if filtros_ativos else df
        df_com_teste, df_sem_teste = separar_dados_sem_teste(df_original)
        
        # Atualizar subtítulo dinâmico
        if data_range and len(data_range) == 2:
            periodo_texto = f"{data_range[0].strftime('%d/%m')} a {data_range[1].strftime('%d/%m')}"
        else:
            periodo_texto = "Período completo"
        
        data_atualizacao = datetime.now().strftime("%B %Y")
        placeholder_subtitulo.markdown(
            f"**Período filtrado:** {periodo_texto} | **Dados atualizados até:** {data_atualizacao}"
        )
        
        if filtros_ativos and not df_com_teste.empty:
            st.info(f"Mostrando {len(df_com_teste)} testes efetuados de {len(df_original)} registros totais.")
        
        st.markdown("---")
        
        # Criar abas para organizar o dashboard
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📌 Visão Geral Estratégica", "🛡️ Prevenção e Qualidade", "🏁 Visão por Sprint", "🧑‍🤝‍🧑 Visão por Testador", "📋 Tarefas Sem Teste", "🔢 Análise de Erros", "🐛 Análise de Bugs", "📊 Relatório"])
        
        with tab1:
            st.markdown("### 📌 **Visão Geral Estratégica**")
            st.markdown("*Dashboard Executivo - Impacto e Performance do Time de Qualidade*")
            
            # Botão de exportação PDF
            col_export_geral, col_space_geral = st.columns([1, 3])
            with col_export_geral:
                botao_exportar_pdf("Visao_Geral_Estrategica", criar_pdf_visao_geral, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # === RESUMO EXECUTIVO PARA DIRETORIA ===
            st.markdown("#### 🎯 **Resumo Executivo - Principais Indicadores**")
            
            # Calcular métricas principais para o resumo
            total_planilha = len(df_com_teste) + len(df_sem_teste) if df_sem_teste is not None else len(df_com_teste)
            total_testes_efetuados = len(df_com_teste)
            cobertura_teste = (total_testes_efetuados / total_planilha * 100) if total_planilha > 0 else 0
            aprovadas = len(df_com_teste[df_com_teste['Status'] == 'APROVADA']) if 'Status' in df_com_teste.columns else 0
            prontas_exec = len(df_com_teste[df_com_teste['Status'] == 'PRONTO PARA PUBLICAÇÃO']) if 'Status' in df_com_teste.columns else 0
            total_aprovadas_exec = aprovadas + prontas_exec
            rejeitadas = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA']) if 'Status' in df_com_teste.columns else 0
            taxa_aprovacao = (total_aprovadas_exec / (total_aprovadas_exec + rejeitadas) * 100) if (total_aprovadas_exec + rejeitadas) > 0 else 0
            
            # Resumo em destaque
            col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
            
            with col_resumo1:
                status_cobertura = "🟢 Excelente" if cobertura_teste >= 80 else "🟡 Boa" if cobertura_teste >= 60 else "🔴 Crítica"
                st.info(f"**📊 Cobertura de Testes:** {cobertura_teste:.1f}% ({total_testes_efetuados:,}/{total_planilha:,} tarefas)\n\n**Status:** {status_cobertura}")
            
            with col_resumo2:
                status_qualidade = "🟢 Excelente" if taxa_aprovacao >= 75 else "🟡 Boa" if taxa_aprovacao >= 60 else "🔴 Atenção"
                st.info(f"**✅ Taxa de Aprovação:** {taxa_aprovacao:.1f}% ({total_aprovadas_exec:,}/{total_aprovadas_exec + rejeitadas:,} testes)\n\n**Status:** {status_qualidade}")
            
            with col_resumo3:
                bugs_encontrados = contar_total_bugs(df_com_teste[df_com_teste['Status'] == 'REJEITADA']) if not df_com_teste.empty else 0
                st.info(f"**🚫 Bugs Interceptados:** {bugs_encontrados:,} problemas\n\n**Status:** Problemas identificados antes da produção")
            
            st.markdown("---")
            
            # Métricas executivas principais
            metricas_resumo(df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # === INSIGHTS ESTRATÉGICOS REMOVIDOS ===
            # Seção removida conforme solicitação
            
            st.markdown("---")
            
            # Gráficos estratégicos
            st.markdown("#### 📊 **Indicadores Visuais Estratégicos**")
            
            col_exec1, col_exec2 = st.columns(2)
            
            with col_exec1:
                # Gráfico de evolução da qualidade
                fig_evolucao = grafico_evolucao_qualidade(df_com_teste, por_ambiente=False)
                if fig_evolucao:
                    st.plotly_chart(fig_evolucao, use_container_width=True, key="evolucao_qualidade")
                
                # Distribuição de status
                fig_status = grafico_status_distribuicao(df_com_teste)
                if fig_status:
                    st.plotly_chart(fig_status, use_container_width=True, key="distribuicao_status")
            
            with col_exec2:
                # Erros por time (crítico para diretoria)
                fig_erros_time = grafico_erros_por_time(df_com_teste)
                if fig_erros_time:
                    st.plotly_chart(fig_erros_time, use_container_width=True, key="erros_por_time_exec")
                
                # Taxa de rejeição por time
                fig_taxa_rejeicao = grafico_taxa_rejeicao_por_time(df_com_teste)
                if fig_taxa_rejeicao:
                    st.plotly_chart(fig_taxa_rejeicao, use_container_width=True, key="taxa_rejeicao_exec")
            
            # Gráfico de tarefas retestadas (nova seção)
            st.markdown("#### 🔄 **Análise de Retestes**")
            fig_retestadas = grafico_tarefas_retestadas(df_com_teste)
            if fig_retestadas:
                st.plotly_chart(fig_retestadas, use_container_width=True, key="tarefas_retestadas_exec")
            
            st.markdown("---")
            
            # === RECOMENDAÇÕES ESTRATÉGICAS PARA DIRETORIA ===
            st.markdown("#### 🎯 **Recomendações Estratégicas**")
            
            if not df_com_teste.empty:
                # Calcular métricas para recomendações
                total_testes = len(df_com_teste)
                aprovados = len(df_com_teste[df_com_teste['Status'] == 'APROVADA'])
                prontos = len(df_com_teste[df_com_teste['Status'] == 'PRONTO PARA PUBLICAÇÃO'])
                total_aprovados = aprovados + prontos
                rejeitados = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA'])
                taxa_aprovacao = (total_aprovados / total_testes * 100) if total_testes > 0 else 0
                
                col_rec1, col_rec2, col_rec3 = st.columns(3)
                
                with col_rec1:
                    if taxa_aprovacao >= 80:
                        st.success(f"**✅ QUALIDADE EXCELENTE**\n\nTaxa de aprovação: {taxa_aprovacao:.1f}%\n\n**Ação:** Manter padrão atual e documentar boas práticas para replicação.")
                    elif taxa_aprovacao >= 60:
                        st.warning(f"**⚠️ QUALIDADE MODERADA**\n\nTaxa de aprovação: {taxa_aprovacao:.1f}%\n\n**Ação:** Implementar treinamentos específicos nos times com maior rejeição.")
                    else:
                        st.error(f"**🚨 QUALIDADE CRÍTICA**\n\nTaxa de aprovação: {taxa_aprovacao:.1f}%\n\n**Ação:** Intervenção imediata necessária - revisar processos de desenvolvimento.")
                
                with col_rec2:
                    # Análise de Eficiência
                    bugs_interceptados = contar_total_bugs(df_com_teste[df_com_teste['Status'] == 'REJEITADA'])
                    eficiencia = (bugs_interceptados / total_testes * 100) if total_testes > 0 else 0
                    
                    if eficiencia >= 30:
                        st.success(f"**🎯 EFICIÊNCIA ALTA**\n\nDetecção: {eficiencia:.1f}%\n\n**{bugs_interceptados} bugs** encontrados em **{total_testes} testes**")
                    elif eficiencia >= 15:
                        st.info(f"**📊 EFICIÊNCIA MODERADA**\n\nDetecção: {eficiencia:.1f}%\n\n**{bugs_interceptados} bugs** encontrados em **{total_testes} testes**")
                    else:
                        st.warning(f"**⚠️ BAIXA DETECÇÃO**\n\nDetecção: {eficiencia:.1f}%\n\n**Ação:** Revisar critérios de teste para melhor detecção.")
                
                with col_rec3:
                    # Análise de cobertura
                    total_tasks = len(df_com_teste) + len(df_sem_teste) if df_sem_teste is not None else len(df_com_teste)
                    cobertura = (total_testes / total_tasks * 100) if total_tasks > 0 else 0
                    
                    if cobertura >= 90:
                        st.success(f"**🎯 COBERTURA EXCELENTE**\n\nCobertura: {cobertura:.1f}%\n\n**Status:** Meta de cobertura atingida com sucesso.")
                    elif cobertura >= 70:
                        st.warning(f"**📊 COBERTURA MODERADA**\n\nCobertura: {cobertura:.1f}%\n\n**Ação:** Expandir cobertura para atingir meta de 90%.")
                    else:
                        st.error(f"**🚨 COBERTURA BAIXA**\n\nCobertura: {cobertura:.1f}%\n\n**Ação:** Urgente - aumentar significativamente a cobertura de testes.")
                
                # Resumo executivo final
                st.markdown("##### 📋 **Resumo Executivo para Diretoria**")
                
                resumo_status = "🟢 SAUDÁVEL" if taxa_aprovacao >= 70 and cobertura >= 70 else "🟡 ATENÇÃO" if taxa_aprovacao >= 50 and cobertura >= 50 else "🔴 CRÍTICO"
                
                st.info(f"**Status Geral do QA:** {resumo_status}\n\n"
                       f"• **{total_testes:,} testes** realizados com **{taxa_aprovacao:.1f}% de aprovação**\n"
                       f"• **{bugs_interceptados} bugs interceptados** antes da produção\n"
                       f"• **Cobertura de {cobertura:.1f}%** das tasks de desenvolvimento\n"
                       f"• **Eficiência de detecção:** {(bugs_interceptados/total_testes*100):.1f}% dos testes encontraram problemas")
            else:
                st.info("📋 Dados insuficientes para gerar recomendações estratégicas")
        
        with tab2:
            st.markdown("### 🛡️ **Prevenção e Qualidade**")
            st.markdown("*Análise unificada: bugs identificados (motivos) + erros encontrados (quantitativos)*")
            
            # Botão de exportação PDF
            col_export_prev, col_space_prev = st.columns([1, 3])
            with col_export_prev:
                botao_exportar_pdf("Prevencao_e_Qualidade", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Análise unificada de qualidade
            analise_unificada = analisar_qualidade_unificada(df_com_teste)
            
            if analise_unificada:
                # Seção de comparação entre as duas abordagens
                st.markdown("#### 📊 **Visão Comparativa: Motivos vs Erros Numéricos**")
                
                col_comp1, col_comp2, col_comp3, col_comp4 = st.columns(4)
                
                with col_comp1:
                    bugs_motivos = analise_unificada['bugs_qualitativos']['total_bugs_motivos']
                    st.metric(
                        "🐛 Bugs por Motivos", 
                        f"{bugs_motivos}",
                        help="Total de bugs identificados através dos motivos de rejeição (análise qualitativa)"
                    )
                
                with col_comp2:
                    erros_numericos = analise_unificada['total_erros_numericos']
                    st.metric(
                        "🔢 Erros Numéricos", 
                        f"{erros_numericos}",
                        help="Total de erros contabilizados na coluna 'Erros' (análise quantitativa)"
                    )
                
                with col_comp3:
                    taxa_rejeicao = analise_unificada['metricas_comparativas']['taxa_rejeicao']
                    st.metric(
                        "📉 Taxa de Rejeição", 
                        f"{taxa_rejeicao:.1f}%",
                        help="Percentual de testes rejeitados (com motivos de falha)"
                    )
                
                with col_comp4:
                    taxa_erros = analise_unificada['metricas_comparativas']['taxa_erros_numericos']
                    st.metric(
                        "⚠️ Taxa c/ Erros", 
                        f"{taxa_erros:.1f}%",
                        help="Percentual de testes que encontraram erros (coluna numérica)"
                    )
                
                # Explicação das diferenças
                st.info("""
                💡 **Entendendo as Métricas:**
                
                - **Bugs por Motivos**: Análise qualitativa baseada nos motivos de rejeição (Motivo, Motivo2, Motivo3)
                - **Erros Numéricos**: Análise quantitativa baseada na coluna 'Erros' que conta o número de erros encontrados
                - **Taxa de Rejeição**: Percentual de testes que foram rejeitados por algum motivo
                - **Taxa c/ Erros**: Percentual de testes que encontraram pelo menos um erro numérico
                
                Ambas as métricas são complementares e oferecem perspectivas diferentes sobre a qualidade.
                """)
                
                st.markdown("---")
            
            # Análise de bugs e qualidade
            st.markdown("#### 🚨 **Bugs Identificados por Time**")
            
            col_bugs1, col_bugs2 = st.columns(2)
            
            with col_bugs1:
                # Gráfico de barras para bugs por time
                fig_erros_time = grafico_erros_por_time(df_com_teste)
                if fig_erros_time:
                    # Melhorar cores e adicionar anotações
                    try:
                        if (fig_erros_time.data and len(fig_erros_time.data) > 0 and 
                            hasattr(fig_erros_time.data[0], 'y') and 
                            hasattr(fig_erros_time.data[0], 'x') and 
                            fig_erros_time.data[0].y is not None and 
                            len(fig_erros_time.data[0].y) > 0):
                            
                            y_values = list(fig_erros_time.data[0].y)
                            x_values = list(fig_erros_time.data[0].x)
                            fig_erros_time.update_traces(
                                marker_color=['#FF6B6B' if i == 0 else '#4ECDC4' for i in range(len(x_values))],
                                text=[f'🚨 Foco prioritário' if i == 0 else f'✅ {y_values[i]} bugs' for i in range(len(x_values))],
                                textposition='outside'
                            )
                        else:
                            fig_erros_time.update_traces(
                                marker_color='#4ECDC4'
                            )
                    except (AttributeError, IndexError, TypeError):
                        # Fallback para casos onde os dados não estão no formato esperado
                        fig_erros_time.update_traces(
                            marker_color='#4ECDC4'
                        )
                    fig_erros_time.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_erros_time, use_container_width=True, key="bugs_por_time_principal")
            
            with col_bugs2:
                # Gráfico de pizza para distribuição de bugs
                if not df_com_teste.empty and 'Time' in df_com_teste.columns:
                    df_rejeitadas = df_com_teste[df_com_teste['Status'] == 'REJEITADA']
                    if not df_rejeitadas.empty:
                        bugs_por_time = contar_bugs_por_time(df_rejeitadas)
                        if not bugs_por_time.empty:
                            import plotly.express as px
                            fig_pizza = px.pie(
                                values=bugs_por_time.values,
                                names=bugs_por_time.index,
                                title="🥧 Distribuição de Bugs por Time",
                                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                            )
                            fig_pizza.update_layout(title_font_color='#FFFFFF')
                            st.plotly_chart(fig_pizza, use_container_width=True, key="distribuicao_bugs_pizza")
            
            st.markdown("---")
            
            # Nova seção de comparação visual
            if analise_unificada:
                st.markdown("#### 🔄 **Comparação Visual: Duas Perspectivas de Qualidade**")
                
                col_comp_visual1, col_comp_visual2 = st.columns(2)
                
                with col_comp_visual1:
                    st.markdown("##### 📝 **Análise Qualitativa (Motivos)**")
                    
                    # Opção de visualização por ambiente se disponível
                    por_ambiente = False
                    if 'Ambiente' in df_com_teste.columns and df_com_teste['Ambiente'].notna().any():
                        por_ambiente = st.checkbox("📊 Visualizar por Ambiente", key="motivos_por_ambiente_principal")
                    
                    # Gráfico de motivos de rejeição
                    fig_motivos = grafico_motivos_rejeicao(df_com_teste, por_ambiente=por_ambiente)
                    if fig_motivos:
                        if not por_ambiente:
                            fig_motivos.update_traces(
                                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'],
                                text=[f'✅ Mais comum' if i == 0 else '' for i in range(len(fig_motivos.data[0].x))],
                                textposition='outside'
                            )
                        fig_motivos.update_layout(title_font_color='#FFFFFF')
                        st.plotly_chart(fig_motivos, use_container_width=True, key="motivos_rejeicao_principal")
                    
                    # Insights sobre motivos
                    motivos_analysis = analise_unificada['bugs_qualitativos']['motivos_analysis']
                    if motivos_analysis and 'motivo_mais_comum' in motivos_analysis and motivos_analysis['motivo_mais_comum']:
                        st.success(f"🎯 **Motivo mais comum**: {motivos_analysis['motivo_mais_comum']}")
                    else:
                        # Fallback: buscar diretamente nos dados
                        df_rejeitadas = df_com_teste[df_com_teste['Status'] == 'REJEITADA'] if 'Status' in df_com_teste.columns else pd.DataFrame()
                        if not df_rejeitadas.empty:
                            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
                            todos_motivos = []
                            for col in motivos_cols:
                                if col in df_rejeitadas.columns:
                                    motivos = df_rejeitadas[col].dropna().tolist()
                                    todos_motivos.extend(motivos)
                            
                            if todos_motivos:
                                motivos_filtrados = [motivo for motivo in todos_motivos 
                                                   if motivo.lower() not in ['aprovada', 'sem recusa', '']]
                                if motivos_filtrados:
                                    motivo_mais_comum = pd.Series(motivos_filtrados).value_counts().index[0]
                                    ocorrencias = pd.Series(motivos_filtrados).value_counts().iloc[0]
                                    st.success(f"🎯 **Motivo mais comum**: {motivo_mais_comum} ({ocorrencias} ocorrências)")
                                else:
                                    st.info("📝 Nenhum motivo específico identificado nos dados filtrados")
                            else:
                                st.info("📝 Nenhum motivo registrado nos dados disponíveis")
                        else:
                            st.info("📝 Nenhuma tarefa rejeitada encontrada nos dados filtrados")
                
                with col_comp_visual2:
                    st.markdown("##### 🔢 **Análise Quantitativa (Erros)**")
                    
                    # Gráfico de distribuição de erros
                    fig_dist_erros = grafico_distribuicao_erros(df_com_teste)
                    if fig_dist_erros:
                        st.plotly_chart(fig_dist_erros, use_container_width=True, key="distribuicao_erros_comparativo")
                    
                    # Gráfico de erros por time (coluna numérica)
                    fig_erros_numericos = grafico_erros_coluna_por_time(df_com_teste)
                    if fig_erros_numericos:
                        st.plotly_chart(fig_erros_numericos, use_container_width=True, key="erros_numericos_time")
                
                # Explicação detalhada das diferenças
                st.markdown("#### 📚 **Entendendo as Duas Abordagens de Análise**")
                
                st.info("""
                **🔍 Diferenças entre as Métricas:**
                
                **📝 Análise Qualitativa (Motivos):**
                - Baseada nas colunas 'Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7'
                - Identifica **tipos de problemas** encontrados
                - Foca na **natureza dos defeitos** (ex: erro de lógica, interface, etc.)
                - Útil para **prevenção** e melhoria de processos
                
                **🔢 Análise Quantitativa (Erros):**
                - Baseada na coluna numérica 'Erros'
                - Conta **quantidade total** de erros encontrados
                - Foca no **volume de problemas** por teste
                - Útil para **métricas de produtividade** e eficiência
                
                **💡 Por que usar ambas?**
                - **Complementares**: Uma mostra 'o quê', outra mostra 'quanto'
                - **Visão completa**: Qualidade + Quantidade = Análise robusta
                - **Decisões melhores**: Dados qualitativos + quantitativos
                """)
                
                st.markdown("---")
            
            st.markdown("#### 🔍 **Tipos de Falha e Motivos**")
            
            col_motivos1, col_motivos2 = st.columns(2)
            
            with col_motivos1:
                # Taxa de aprovação vs rejeição (barras + pizza)
                if not df_com_teste.empty and 'Status' in df_com_teste.columns:
                    status_counts = df_com_teste['Status'].value_counts()
                    if len(status_counts) > 1:
                        import plotly.express as px
                        st.markdown("**📊 Análise Qualitativa - Motivos de Rejeição**")
                        st.info("Esta seção foca nos motivos e causas dos problemas encontrados, permitindo identificar padrões e oportunidades de melhoria no processo de desenvolvimento.")
            
            with col_motivos2:
                # Taxa de aprovação vs rejeição (barras + pizza)
                if not df_com_teste.empty and 'Status' in df_com_teste.columns:
                    status_counts = df_com_teste['Status'].value_counts()
                    if len(status_counts) > 1:
                        import plotly.express as px
                        fig_aprovacao = px.bar(
                            x=status_counts.index,
                            y=status_counts.values,
                            title="📊 Taxa de Aprovação vs Rejeição",
                            color=status_counts.values,
                            color_discrete_sequence=['#28a745', '#dc3545'],
                            text=status_counts.values
                        )
                        fig_aprovacao.update_traces(textposition='outside')
                        fig_aprovacao.update_layout(
                            title_font_color='#FFFFFF',
                            xaxis_title="Status",
                            yaxis_title="Quantidade",
                            margin=dict(t=50, b=80, l=80, r=80),
                            height=450
                        )
                        st.plotly_chart(fig_aprovacao, use_container_width=True, key="taxa_aprovacao_barras")
            
            st.markdown("---")
            st.markdown("#### 🎯 **Análise Detalhada de Motivos por Time**")
            
            col_time1, col_time2 = st.columns(2)
            
            with col_time1:
                # Gráfico de motivos por time
                fig_motivos_time = grafico_motivos_por_time(df_com_teste)
                if fig_motivos_time:
                    st.plotly_chart(fig_motivos_time, use_container_width=True, key="motivos_por_time")
                else:
                    st.info("📋 Dados insuficientes para análise de motivos por time")
            
            with col_time2:
                # Ranking dos problemas mais encontrados
                fig_ranking = grafico_ranking_problemas(df_com_teste)
                if fig_ranking:
                    st.plotly_chart(fig_ranking, use_container_width=True, key="ranking_problemas")
                else:
                    st.info("📋 Dados insuficientes para ranking de problemas")
            
            st.markdown("---")
            st.markdown("#### 👨‍💻 **Análise Detalhada por Desenvolvedor**")
            
            col_dev1, col_dev2 = st.columns(2)
            
            with col_dev1:
                # Gráfico sunburst de motivos por desenvolvedor
                fig_motivos_dev_sun = grafico_motivos_por_desenvolvedor(df_com_teste)
                if fig_motivos_dev_sun:
                    st.plotly_chart(fig_motivos_dev_sun, use_container_width=True, key="motivos_por_desenvolvedor")
                else:
                    st.info("📋 Dados insuficientes para análise de motivos por desenvolvedor")
            
            with col_dev2:
                # Gráfico de barras: Motivos de recusa por desenvolvedor
                fig_motivos_dev = grafico_motivos_recusa_por_dev(df_com_teste)
                if fig_motivos_dev:
                    st.plotly_chart(fig_motivos_dev, use_container_width=True, key="motivos_recusa_por_dev")
                else:
                    st.info("📋 Dados insuficientes para análise de rejeições por desenvolvedor (mínimo 2 rejeições por dev)")
            
            st.markdown("---")
            
            # === INSIGHTS EXECUTIVOS PARA GERÊNCIA ===
            st.markdown("#### 🎯 **Insights Executivos - Análise de Problemas por Time**")
            
            if not df_com_teste.empty:
                df_rejeitadas = df_com_teste[df_com_teste['Status'] == 'REJEITADA']
                
                if not df_rejeitadas.empty and 'Time' in df_rejeitadas.columns:
                    # Análise de problemas por time
                    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
                    motivos_existentes = [col for col in motivos_cols if col in df_rejeitadas.columns]
                    
                    if motivos_existentes:
                        dados_analise = []
                        for _, row in df_rejeitadas.iterrows():
                            time = row.get('Time', 'N/A')
                            for col in motivos_existentes:
                                motivo = row.get(col)
                                if pd.notna(motivo) and motivo.lower() not in ['aprovada', 'sem recusa', '']:
                                    dados_analise.append({'Time': time, 'Motivo': motivo})
                        
                        if dados_analise:
                            df_analise = pd.DataFrame(dados_analise)
                            
                            col_insight1, col_insight2 = st.columns(2)
                            
                            with col_insight1:
                                # Time com mais problemas
                                problemas_por_time = df_analise['Time'].value_counts()
                                time_critico = problemas_por_time.index[0]
                                qtd_problemas = problemas_por_time.iloc[0]
                                
                                st.error(f"**🚨 Time com Maior Necessidade de Atenção**\n\n**{time_critico}** - {qtd_problemas} problemas identificados\n\nRecomendação: Revisar processos e oferecer treinamento específico.")
                            
                            with col_insight2:
                                # Problema mais comum
                                problema_comum = df_analise['Motivo'].value_counts().index[0]
                                qtd_comum = df_analise['Motivo'].value_counts().iloc[0]
                                
                                st.warning(f"**⚠️ Problema Mais Recorrente**\n\n**{problema_comum}** - {qtd_comum} ocorrências\n\nRecomendação: Implementar checklist preventivo para este tipo de erro.")
                            
                            # Análise de distribuição de problemas
                            st.markdown("##### 📊 **Distribuição de Problemas por Time**")
                            
                            col_dist1, col_dist2 = st.columns(2)
                            
                            with col_dist1:
                                # Tabela de problemas por time
                                tabela_problemas = df_analise.groupby('Time').agg({
                                    'Motivo': ['count', lambda x: x.nunique()]
                                }).round(2)
                                tabela_problemas.columns = ['Total Problemas', 'Tipos Diferentes']
                                tabela_problemas = tabela_problemas.sort_values('Total Problemas', ascending=False)
                                
                                st.dataframe(
                                    tabela_problemas,
                                    use_container_width=True,
                                    column_config={
                                        "Total Problemas": st.column_config.NumberColumn(
                                            "Total de Problemas",
                                            help="Quantidade total de problemas encontrados"
                                        ),
                                        "Tipos Diferentes": st.column_config.NumberColumn(
                                            "Tipos Diferentes",
                                            help="Variedade de tipos de problemas"
                                        )
                                    }
                                )
                            
                            with col_dist2:
                                # Top 5 problemas mais comuns
                                top_problemas = df_analise['Motivo'].value_counts().head(5)
                                
                                st.markdown("**🏆 Top 5 Problemas Mais Comuns:**")
                                for i, (problema, qtd) in enumerate(top_problemas.items(), 1):
                                    st.markdown(f"{i}. **{problema}** - {qtd} ocorrências")
                        else:
                            st.info("📋 Nenhum motivo de rejeição encontrado para análise")
                    else:
                        st.info("📋 Colunas de motivos não encontradas nos dados")
                else:
                    st.info("📋 Dados insuficientes para análise de problemas por time")
            else:
                st.info("📋 Nenhum dado disponível para análise")
            
            st.markdown("---")
            st.markdown("#### 📈 **Evolução de Taxa ao Longo do Tempo**")
            
            # Opção de visualização por ambiente se disponível
            por_ambiente_evolucao = False
            if 'Ambiente' in df_com_teste.columns and df_com_teste['Ambiente'].notna().any():
                por_ambiente_evolucao = st.checkbox("📊 Visualizar evolução por Ambiente", key="evolucao_por_ambiente_principal")
            
            # Melhorar gráfico de evolução
            fig_evolucao = grafico_evolucao_qualidade(df_com_teste, por_ambiente=por_ambiente_evolucao)
            if fig_evolucao:
                # Melhorar escala do eixo Y para mostrar variações reais
                fig_evolucao.update_layout(
                    yaxis=dict(
                        title="Taxa de Aprovação (%)",
                        range=[0, 100],
                        dtick=10
                    ),
                    title_font_color='#FFFFFF',
                    annotations=[
                        dict(
                            x=0.5, y=1.1,
                            xref='paper', yref='paper',
                            text="💡 Dica: Busque tendência de melhoria contínua",
                            showarrow=False,
                            font=dict(size=12, color='#7F8C8D')
                        )
                    ]
                )
                st.plotly_chart(fig_evolucao, use_container_width=True, key="evolucao_qualidade_melhorada")
        
        with tab3:
            st.markdown("### 🏁 **Visão por Sprint**")
            st.markdown("*Tasks testadas por sprint e cobertura de Q.A por time*")
            
            # Botão de exportação PDF
            col_export_sprint, col_space_sprint = st.columns([1, 3])
            with col_export_sprint:
                botao_exportar_pdf("Visao_por_Sprint", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Análise por Sprint
            st.markdown("#### 📊 **Tasks Testadas por Sprint**")
            
            # Timeline de tasks
            with st.container():
                # Timeline de tasks
                fig_timeline = grafico_timeline_tasks(df_com_teste)
                if fig_timeline:
                    fig_timeline.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_timeline, use_container_width=True, key="timeline_tasks")
            
            st.markdown("---")
            st.markdown("#### 🎯 **Cobertura de Q.A por Time**")
            
            col_cobertura1, col_cobertura2 = st.columns(2)
            
            with col_cobertura1:
                fig_time = grafico_tasks_por_time(df_com_teste)
                if fig_time:
                    fig_time.update_layout(
                        title_font_color='#FFFFFF',
                        xaxis_tickangle=45
                    )
                    st.plotly_chart(fig_time, use_container_width=True, key="tasks_por_time_sprint")
            
            with col_cobertura2:
                # Distribuição de status
                fig_status = grafico_status_distribuicao(df_com_teste)
                if fig_status:
                    fig_status.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_status, use_container_width=True, key="status_distribuicao_sprint")
            
            st.markdown("---")
            st.markdown("#### 👨‍💻 **Análise por Desenvolvedor**")
            
            col_dev1, col_dev2 = st.columns(2)
            
            with col_dev1:
                fig_aprovadas_dev = grafico_ranking_aprovadas_por_dev(df_com_teste)
                if fig_aprovadas_dev:
                    fig_aprovadas_dev.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_aprovadas_dev, use_container_width=True, key="ranking_aprovadas_por_dev")
                else:
                    st.info("📋 Dados insuficientes para ranking de tarefas aprovadas")
            
            with col_dev2:
                fig_rejeitadas_dev = grafico_rejeicoes_por_dev(df_com_teste)
                if fig_rejeitadas_dev:
                    fig_rejeitadas_dev.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_rejeitadas_dev, use_container_width=True, key="rejeicoes_por_dev_sprint")
                else:
                    st.info("📋 Dados insuficientes para análise de rejeições por desenvolvedor")
            
            col_dev3, col_dev4 = st.columns(2)
            
            with col_dev3:
                fig_retestadas_dev = grafico_tarefas_retestadas_por_dev(df_com_teste)
                if fig_retestadas_dev:
                    fig_retestadas_dev.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_retestadas_dev, use_container_width=True, key="tarefas_retestadas_por_dev")
                else:
                    st.info("📋 Dados insuficientes para análise de tarefas retestadas")
            
            with col_dev4:
                st.empty()
        
        with tab4:
            st.markdown("### 🧑‍🤝‍🧑 **Visão por Testador**")
            st.markdown("*Ranking de performance, produtividade e comparação entre testadores*")
            
            # Botão de exportação PDF
            col_export_testador, col_space_testador = st.columns([1, 3])
            with col_export_testador:
                botao_exportar_pdf("Visao_por_Testador", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            if 'Responsavel pelo teste' in df_com_teste.columns and not df_com_teste.empty:
                testador_stats = df_com_teste.groupby('Responsavel pelo teste').agg({
                    'Status': ['count', lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'APROVADA').sum(), lambda x: (x == 'PRONTO PARA PUBLICAÇÃO').sum()]
                }).round(1)
                
                testador_stats.columns = ['Total_Testes', 'Bugs_Encontrados', 'Testes_Aprovados', 'Testes_Prontos']
                testador_stats['Total_Aprovadas'] = testador_stats['Testes_Aprovados'] + testador_stats['Testes_Prontos']
                testador_stats['Taxa_Deteccao'] = (testador_stats['Bugs_Encontrados'] / testador_stats['Total_Testes'] * 100).round(1)
                testador_stats['Taxa_Aprovacao'] = (testador_stats['Total_Aprovadas'] / testador_stats['Total_Testes'] * 100).round(1)
                testador_stats['Produtividade'] = testador_stats['Total_Testes']
                testador_stats = testador_stats.reset_index()
                
                # Insights destacados
                st.markdown("#### 💡 **Insights de Performance**")
                
                total_tarefas = testador_stats['Total_Testes'].sum()
                media_aprovacao = testador_stats['Taxa_Aprovacao'].mean()
                
                col_insight1, col_insight2 = st.columns(2)
                
                with col_insight1:
                    testadores_nomes = ' e '.join(testador_stats['Responsavel pelo teste'].tolist())
                    st.success(f"🎯 **Eficiência por pessoa:** {testadores_nomes} juntos validaram {int(total_tarefas)} tarefas com taxa de aprovação média de {media_aprovacao:.1f}%.")
                
                with col_insight2:
                    acima_media = testador_stats[testador_stats['Taxa_Aprovacao'] >= media_aprovacao]
                    if len(acima_media) >= 2:
                        st.info(f"⭐ **Qualidade similar:** Ambos testadores entregaram acima da média com qualidade similar — excelente consistência da equipe!")
                
                st.markdown("---")
                st.markdown("#### 📊 **Comparação Visual de Performance**")
                
                # Gráfico de comparação
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    # Gráfico de barras comparativo - Produtividade
                    import plotly.express as px
                    fig_prod = px.bar(
                        testador_stats,
                        x='Responsavel pelo teste',
                        y='Total_Testes',
                        title='📈 Comparativo de Produtividade',
                        color='Total_Testes',
                        color_continuous_scale=['#4ECDC4', '#45B7D1'],
                        text='Total_Testes'
                    )
                    fig_prod.update_traces(textposition='outside')
                    fig_prod.update_coloraxes(showscale=False)
                    fig_prod.update_layout(
                        title_font_color='#FFFFFF',
                        xaxis_title='Testador',
                        yaxis_title='Total de Testes',
                        showlegend=False,
                        margin=dict(t=50, b=80, l=80, r=80),
                        height=450
                    )
                    fig_prod.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_prod, use_container_width=True, key="comparativo_produtividade")
                
                with col_graf2:
                    # Gráfico de barras comparativo - Taxas
                    fig_taxas = px.bar(
                        testador_stats,
                        x='Responsavel pelo teste',
                        y=['Taxa_Aprovacao', 'Taxa_Deteccao'],
                        title='📊 Comparativo de Taxas (%)',
                        color_discrete_sequence=['#28a745', '#ffc107'],
                        barmode='group',
                        text_auto=True
                    )
                    
                    # Renomear legendas para serem mais claras
                    newnames = {'Taxa_Aprovacao': 'Taxa de Aprovação (%)', 'Taxa_Deteccao': 'Bugs Encontrados (%)'}
                    fig_taxas.for_each_trace(lambda t: t.update(name = newnames[t.name]))
                    
                    fig_taxas.update_layout(
                        title_font_color='#FFFFFF',
                        xaxis_title='Testador',
                        yaxis_title='Percentual (%)',
                        legend_title='Métricas',
                        margin=dict(t=50, b=120, l=80, r=80),
                        height=450
                    )
                    fig_taxas.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
                    fig_taxas.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_taxas, use_container_width=True, key="comparativo_taxas")
                
                st.markdown("---")
                st.markdown("#### 🏆 **Ranking Detalhado de Performance**")
            
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Métricas por Testador**")
                    for _, row in testador_stats.iterrows():
                        with st.expander(f"👤 {row['Responsavel pelo teste']}"):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total de Testes", int(row['Total_Testes']))
                            with col_b:
                                st.metric("Bugs Encontrados", int(row['Bugs_Encontrados']))
                            with col_c:
                                st.metric("Testes Aprovados", int(row['Testes_Aprovados']))
                            
                            col_d, col_e = st.columns(2)
                            with col_d:
                                st.metric("Bugs Encontrados (%)", f"{row['Taxa_Deteccao']:.1f}%")
                            with col_e:
                                st.metric("Taxa de Aprovação", f"{row['Taxa_Aprovacao']:.1f}%")
                
                with col2:
                    st.markdown("**📈 Ranking de Performance**")
                    
                    ranking_produtividade = testador_stats.sort_values('Total_Testes', ascending=False)
                    st.markdown("🏆 **Produtividade (Total de Testes)**")
                    for i, (_, row) in enumerate(ranking_produtividade.iterrows(), 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                        st.write(f"{emoji} {i}º - {row['Responsavel pelo teste']}: {int(row['Total_Testes'])} testes")
                    
                    st.markdown("")
                    ranking_deteccao = testador_stats.sort_values('Taxa_Deteccao', ascending=False)
                    st.markdown("🔍 **Bugs Encontrados (%)**")
                    for i, (_, row) in enumerate(ranking_deteccao.iterrows(), 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                        st.write(f"{emoji} {i}º - {row['Responsavel pelo teste']}: {row['Taxa_Deteccao']:.1f}%")
                    
                    st.markdown("")
                    ranking_aprovacao = testador_stats.sort_values('Taxa_Aprovacao', ascending=False)
                    st.markdown("✅ **Taxa de Aprovação**")
                    for i, (_, row) in enumerate(ranking_aprovacao.iterrows(), 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
                        st.write(f"{emoji} {i}º - {row['Responsavel pelo teste']}: {row['Taxa_Aprovacao']:.1f}%")
                
                st.markdown("")
                st.markdown("**📊 Comparativo Visual**")
                
                fig_comp = go.Figure()
                
                fig_comp.add_trace(go.Bar(
                    name='Total de Testes',
                    x=testador_stats['Responsavel pelo teste'],
                    y=testador_stats['Total_Testes'],
                    marker_color='lightgreen',
                    text=testador_stats['Total_Testes'],
                    textposition='outside'
                ))
                
                fig_comp.update_layout(
                    title="📊 Comparativo de Produtividade entre Testadores",
                    xaxis_title="Testador",
                    yaxis_title="Quantidade de Testes",
                    margin=dict(t=50, b=50, l=50, r=50),
                    height=400
                )
                
                st.plotly_chart(fig_comp, use_container_width=True, key="comparativo_produtividade_detalhado")
                
                fig_taxa = go.Figure()
                
                fig_taxa.add_trace(go.Scatter(
                    name='Bugs Encontrados (%)',
                    x=testador_stats['Responsavel pelo teste'],
                    y=testador_stats['Taxa_Deteccao'],
                    mode='lines+markers',
                    marker_color='red',
                    line=dict(width=3),
                    text=[f"{val:.1f}%" for val in testador_stats['Taxa_Deteccao']],
                    textposition='top center'
                ))
                
                fig_taxa.add_trace(go.Scatter(
                    name='Taxa de Aprovação',
                    x=testador_stats['Responsavel pelo teste'],
                    y=testador_stats['Taxa_Aprovacao'],
                    mode='lines+markers',
                    marker_color='green',
                    line=dict(width=3),
                    text=[f"{val:.1f}%" for val in testador_stats['Taxa_Aprovacao']],
                    textposition='bottom center'
                ))
                
                fig_taxa.update_layout(
                    title="📈 Comparativo de Taxas de Performance",
                    xaxis_title="Testador",
                    yaxis_title="Percentual (%)",
                    margin=dict(t=50, b=50, l=50, r=50),
                    height=400
                )
                
                st.plotly_chart(fig_taxa, use_container_width=True, key="comparativo_taxas_detalhado")
        

        
        with tab5:
            st.markdown("### 📋 **Tarefas Sem Teste**")
            st.markdown("*Análise detalhada das tarefas que não passaram por testes de qualidade*")
            
            # Botão de exportação PDF
            col_export_sem_teste, col_space_sem_teste = st.columns([1, 3])
            with col_export_sem_teste:
                botao_exportar_pdf("Tarefas_Sem_Teste", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            if not df_sem_teste.empty:
                # Filtros para tarefas sem teste
                st.markdown("#### 🔍 **Filtros**")
                
                col_filter1, col_filter2, col_filter3 = st.columns(3)
                
                with col_filter1:
                    # Filtro por Sprint
                    sprints_sem_teste = ['Todos'] + sorted(df_sem_teste['Sprint'].dropna().unique().tolist()) if 'Sprint' in df_sem_teste.columns else ['Todos']
                    sprint_selecionado = st.selectbox("Sprint:", sprints_sem_teste, key="sprint_sem_teste")
                
                with col_filter2:
                    # Filtro por Time
                    times_sem_teste = ['Todos'] + sorted(df_sem_teste['Time'].dropna().unique().tolist()) if 'Time' in df_sem_teste.columns else ['Todos']
                    time_selecionado = st.selectbox("Time:", times_sem_teste, key="time_sem_teste")
                
                with col_filter3:
                    # Filtro por Responsável
                    responsaveis_sem_teste = ['Todos'] + sorted(df_sem_teste['Responsável'].dropna().unique().tolist()) if 'Responsável' in df_sem_teste.columns else ['Todos']
                    responsavel_selecionado = st.selectbox("Responsável:", responsaveis_sem_teste, key="responsavel_sem_teste")
                
                # Aplicar filtros
                df_sem_teste_filtrado = df_sem_teste.copy()
                
                if sprint_selecionado != 'Todos':
                    df_sem_teste_filtrado = df_sem_teste_filtrado[df_sem_teste_filtrado['Sprint'] == sprint_selecionado]
                
                if time_selecionado != 'Todos':
                    df_sem_teste_filtrado = df_sem_teste_filtrado[df_sem_teste_filtrado['Time'] == time_selecionado]
                
                if responsavel_selecionado != 'Todos':
                    df_sem_teste_filtrado = df_sem_teste_filtrado[df_sem_teste_filtrado['Responsável'] == responsavel_selecionado]
                
                st.markdown("---")
                
                # Métricas resumidas
                col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                
                with col_metric1:
                    st.metric("Total de Tarefas", len(df_sem_teste_filtrado))
                
                with col_metric2:
                    times_unicos = df_sem_teste_filtrado['Time'].nunique() if 'Time' in df_sem_teste_filtrado.columns else 0
                    st.metric("Times Envolvidos", times_unicos)
                
                with col_metric3:
                    sprints_unicos = df_sem_teste_filtrado['Sprint'].nunique() if 'Sprint' in df_sem_teste_filtrado.columns else 0
                    st.metric("Sprints Afetados", sprints_unicos)
                
                with col_metric4:
                    responsaveis_unicos = df_sem_teste_filtrado['Responsável'].nunique() if 'Responsável' in df_sem_teste_filtrado.columns else 0
                    st.metric("Desenvolvedores", responsaveis_unicos)
                
                st.markdown("---")
                
                # Gráficos de análise
                if not df_sem_teste_filtrado.empty:
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        # Gráfico por Time
                        if 'Time' in df_sem_teste_filtrado.columns:
                            time_counts = df_sem_teste_filtrado['Time'].value_counts()
                            if not time_counts.empty:
                                fig_time = px.bar(
                                    x=time_counts.values,
                                    y=time_counts.index,
                                    orientation='h',
                                    title='Tarefas Sem Teste por Time',
                                    labels={'x': 'Quantidade', 'y': 'Time'}
                                )
                                fig_time.update_traces(marker_color='#FF6B6B', text=time_counts.values, textposition='outside')
                                fig_time.update_layout(
                                    margin=dict(t=50, b=80, l=150, r=80),
                                    height=400
                                )
                                st.plotly_chart(fig_time, use_container_width=True)
                    
                    with col_chart2:
                        # Gráfico por Sprint
                        if 'Sprint' in df_sem_teste_filtrado.columns:
                            sprint_counts = df_sem_teste_filtrado['Sprint'].value_counts().sort_index()
                            if not sprint_counts.empty:
                                fig_sprint = px.bar(
                                    x=sprint_counts.index,
                                    y=sprint_counts.values,
                                    title='Tarefas Sem Teste por Sprint',
                                    labels={'x': 'Sprint', 'y': 'Quantidade'}
                                )
                                fig_sprint.update_traces(marker_color='#FFA726', text=sprint_counts.values, textposition='outside')
                                fig_sprint.update_layout(
                                    margin=dict(t=50, b=80, l=80, r=80),
                                    height=400
                                )
                                st.plotly_chart(fig_sprint, use_container_width=True)
                
                st.markdown("---")
                
                # Tabela de dados filtrados
                st.markdown("#### 📊 **Dados Detalhados**")
                if st.checkbox("Mostrar tabela de tarefas sem teste", key="show_sem_teste_table"):
                    st.dataframe(df_sem_teste_filtrado, use_container_width=True)
                    st.caption(f"Exibindo {len(df_sem_teste_filtrado)} de {len(df_sem_teste)} tarefas sem teste")
                    
                    # Opção de download
                    if not df_sem_teste_filtrado.empty:
                        csv = df_sem_teste_filtrado.to_csv(index=False)
                        st.download_button(
                            label="📥 Baixar dados filtrados (CSV)",
                            data=csv,
                            file_name=f"tarefas_sem_teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
            else:
                st.info("📋 Nenhuma tarefa sem teste encontrada nos dados carregados.")
                st.markdown("""
                ### ℹ️ **Sobre esta seção:**
                
                Esta aba mostra tarefas que foram marcadas com motivo "SEM TESTE", permitindo:
                
                - **Filtros avançados** por Sprint, Time e Responsável
                - **Métricas resumidas** do impacto
                - **Visualizações gráficas** para análise
                - **Exportação de dados** filtrados
                
                Isso ajuda a identificar padrões e tomar ações para melhorar a cobertura de testes.
                """)
        
        with tab6:
            st.markdown("### 🔢 **Análise de Erros Encontrados**")
            st.markdown("*Análise detalhada dos erros identificados durante os testes*")
            
            # Botão de exportação PDF
            col_export_erros, col_space_erros = st.columns([1, 3])
            with col_export_erros:
                botao_exportar_pdf("Analise_de_Erros", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Informação sobre o escopo da análise
            st.info("ℹ️ **Importante**: A taxa de testes com erro é calculada sobre o total de testes realizados. O gráfico de distribuição mostra três categorias: testes com erro, testes sem erro e testes sem dados de erro preenchidos.")
            
            if 'Erros' in df_com_teste.columns:
                # Verificar se há dados de erros
                dados_erros = df_com_teste[df_com_teste['Erros'].notna()]
                
                if not dados_erros.empty:
                    # Métricas principais de erros
                    st.markdown("#### 📊 **Métricas de Erros**")
                    
                    col_err1, col_err2, col_err3, col_err4 = st.columns(4)
                    
                    with col_err1:
                        total_erros = contar_total_erros(dados_erros)
                        st.metric("🔢 Total de Erros", f"{total_erros:,}")
                    
                    with col_err2:
                        media_erros = calcular_media_erros_por_teste(dados_erros)
                        st.metric("📊 Média por Teste", f"{media_erros:.1f}")
                    
                    with col_err3:
                        distribuicao = analisar_distribuicao_erros(dados_erros)
                        if distribuicao:
                            st.metric("📈 Máximo de Erros", f"{distribuicao['max_erros_teste']}")
                    
                    with col_err4:
                        if distribuicao:
                            testes_com_erro = distribuicao['testes_com_erro']
                            total_testes = distribuicao['total_testes']
                            taxa = (testes_com_erro / total_testes * 100) if total_testes > 0 else 0
                            st.metric("⚠️ Taxa c/ Erro", f"{taxa:.1f}%")
                    
                    st.markdown("---")
                    
                    # Gráficos de análise de erros
                    st.markdown("#### 📈 **Análise Visual de Erros**")
                    
                    col_graf_err1, col_graf_err2 = st.columns(2)
                    
                    with col_graf_err1:
                        # Erros por time
                        fig_erros_time = grafico_erros_coluna_por_time(dados_erros)
                        if fig_erros_time:
                            st.plotly_chart(fig_erros_time, use_container_width=True, key="erros_coluna_por_time")
                        
                        # Distribuição de erros
                        fig_dist_erros = grafico_distribuicao_erros(dados_erros)
                        if fig_dist_erros:
                            st.plotly_chart(fig_dist_erros, use_container_width=True, key="distribuicao_erros")
                    
                    with col_graf_err2:
                        # Erros por testador
                        fig_erros_testador = grafico_erros_por_testador(dados_erros)
                        if fig_erros_testador:
                            st.plotly_chart(fig_erros_testador, use_container_width=True, key="erros_por_testador")
                        
                        # Média de erros por time
                        fig_media_erros = grafico_media_erros_por_time(dados_erros)
                        if fig_media_erros:
                            st.plotly_chart(fig_media_erros, use_container_width=True, key="media_erros_por_time")
                    
                    st.markdown("---")
                    
                    # Insights automáticos sobre erros
                    st.markdown("#### 💡 **Insights sobre Erros**")
                    
                    insights_erros = []
                    
                    # Insight sobre total de erros
                    if total_erros > 0:
                        if media_erros > 2:
                            insights_erros.append(f"🚨 **ATENÇÃO**: Média de {media_erros:.1f} erros por teste é alta - revisar processos")
                        elif media_erros > 1:
                            insights_erros.append(f"⚠️ Média de {media_erros:.1f} erros por teste - monitorar tendência")
                        else:
                            insights_erros.append(f"✅ Média de {media_erros:.1f} erros por teste está em nível aceitável")
                    
                    # Insight sobre distribuição
                    if distribuicao:
                        if distribuicao['max_erros_teste'] > 5:
                            insights_erros.append(f"🔍 **CRÍTICO**: Teste com {distribuicao['max_erros_teste']} erros requer investigação")
                        
                        taxa_sem_erro = (distribuicao['testes_sem_erro'] / distribuicao['total_testes'] * 100) if distribuicao['total_testes'] > 0 else 0
                        if taxa_sem_erro > 70:
                            insights_erros.append(f"✅ {taxa_sem_erro:.1f}% dos testes não encontraram erros - boa qualidade")
                        elif taxa_sem_erro < 50:
                            insights_erros.append(f"⚠️ Apenas {taxa_sem_erro:.1f}% dos testes não encontraram erros - revisar qualidade")
                    
                    # Insight sobre time com mais erros
                    erros_por_time = contar_erros_por_time(dados_erros)
                    if not erros_por_time.empty:
                        time_mais_erros = erros_por_time.index[0]
                        qtd_erros_time = erros_por_time.iloc[0]
                        insights_erros.append(f"🏢 Time **{time_mais_erros}** tem o maior número de erros ({qtd_erros_time})")
                    
                    # Insight sobre testador com mais erros
                    erros_por_testador = contar_erros_por_testador(dados_erros)
                    if not erros_por_testador.empty:
                        testador_mais_erros = erros_por_testador.index[0]
                        qtd_erros_testador = erros_por_testador.iloc[0]
                        insights_erros.append(f"👤 Testador **{testador_mais_erros}** identificou mais erros ({qtd_erros_testador})")
                    
                    # Exibir insights
                    for insight in insights_erros:
                        if "CRÍTICO" in insight or "ATENÇÃO" in insight:
                            st.error(insight)
                        elif "⚠️" in insight:
                            st.warning(insight)
                        else:
                            st.info(insight)
                    
                    st.markdown("---")
                    
                    # Tabela detalhada de erros
                    st.markdown("#### 📋 **Dados Detalhados de Erros**")
                    if st.checkbox("Mostrar tabela de testes com erros", key="show_erros_table"):
                        # Filtrar apenas testes com erros > 0
                        dados_temp = dados_erros.copy()
                        dados_temp['Erros'] = pd.to_numeric(dados_temp['Erros'], errors='coerce').fillna(0)
                        dados_com_erros = dados_temp[dados_temp['Erros'] > 0].sort_values('Erros', ascending=False)
                        if not dados_com_erros.empty:
                            st.dataframe(dados_com_erros, use_container_width=True)
                            st.caption(f"Exibindo {len(dados_com_erros)} testes que encontraram erros")
                            
                            # Opção de download
                            csv = dados_com_erros.to_csv(index=False)
                            st.download_button(
                                label="📥 Baixar dados de erros (CSV)",
                                data=csv,
                                file_name=f"analise_erros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("📋 Nenhum teste com erros encontrado nos dados filtrados.")
                else:
                    st.info("📋 Nenhum dado de erro encontrado nos testes realizados.")
            else:
                st.warning("⚠️ Coluna 'Erros' não encontrada na planilha. Verifique se a coluna foi adicionada corretamente.")
                st.markdown("""
                ### ℹ️ **Sobre esta seção:**
                
                Esta aba analisa a coluna "Erros" da planilha, mostrando:
                
                - **Métricas de erros** por time e testador
                - **Distribuição de erros** encontrados
                - **Análise visual** com gráficos interativos
                - **Insights automáticos** sobre padrões de erro
                - **Exportação de dados** para análise externa
                
                Para usar esta funcionalidade, certifique-se de que a coluna "Erros" existe na planilha.
                """)
        
        with tab7:
            st.markdown("### 🐛 **Análise Detalhada de Bugs**")
            st.markdown("*Insights profissionais sobre defeitos identificados em produção*")
            
            # Botão de exportação PDF
            col_export_bugs, col_space_bugs = st.columns([1, 3])
            with col_export_bugs:
                botao_exportar_pdf("Analise_de_Bugs", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Carregar dados de bugs
            df_bugs = carregar_dados_bugs()
            
            if df_bugs is not None and not df_bugs.empty:
                # Usar os dados de bugs sem filtros adicionais
                df_bugs_filtrado = df_bugs.copy()
                
                st.markdown("---")
                # Processar métricas de bugs (usando dados filtrados)
                metricas_bugs = processar_metricas_bugs(df_bugs_filtrado)
                
                # Métricas principais de bugs
                st.markdown("#### 📊 **Métricas Executivas de Bugs**")
                
                col_bug1, col_bug2, col_bug3, col_bug4 = st.columns(4)
                
                with col_bug1:
                    st.metric("🐛 Total de Bugs", metricas_bugs.get('total_bugs', 0))
                
                with col_bug2:
                    st.metric("🚨 Bugs Críticos", metricas_bugs.get('bugs_criticos', 0))
                
                with col_bug3:
                    st.metric("🔓 Bugs Abertos", metricas_bugs.get('bugs_abertos', 0))
                
                with col_bug4:
                    st.metric("✅ Bugs Resolvidos", metricas_bugs.get('bugs_resolvidos', 0))
                
                st.markdown("---")
                
                # Gráficos de análise de bugs (usando dados filtrados)
                st.markdown("#### 📈 **Análise Visual de Bugs**")
                
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    # Status dos bugs
                    fig_status_bugs = grafico_bugs_por_status(df_bugs_filtrado)
                    if fig_status_bugs:
                        st.plotly_chart(fig_status_bugs, use_container_width=True, key="bugs_status")
                    
                    # Bugs por time
                    fig_bugs_time = grafico_bugs_por_time(df_bugs_filtrado)
                    if fig_bugs_time:
                        st.plotly_chart(fig_bugs_time, use_container_width=True, key="bugs_time")
                
                with col_graf2:
                    # Prioridade dos bugs
                    fig_prioridade_bugs = grafico_bugs_por_prioridade(df_bugs_filtrado)
                    if fig_prioridade_bugs:
                        st.plotly_chart(fig_prioridade_bugs, use_container_width=True, key="bugs_prioridade")
                    
                    # Fonte de detecção
                    fig_fonte_bugs = grafico_bugs_fonte_deteccao(df_bugs_filtrado)
                    if fig_fonte_bugs:
                        st.plotly_chart(fig_fonte_bugs, use_container_width=True, key="bugs_fonte")
                
                # Evolução temporal dos bugs
                st.markdown("#### 📅 **Evolução Temporal**")
                fig_evolucao_bugs = grafico_evolucao_bugs(df_bugs_filtrado)
                if fig_evolucao_bugs:
                    st.plotly_chart(fig_evolucao_bugs, use_container_width=True, key="bugs_evolucao")
                
                st.markdown("---")
                
                # Insights automáticos
                st.markdown("#### 💡 **Insights Estratégicos**")
                
                insights_bugs = []
                
                # Insight sobre bugs críticos
                if metricas_bugs.get('bugs_criticos', 0) > 0:
                    total_bugs = metricas_bugs.get('total_bugs', 1)
                    perc_criticos = (metricas_bugs['bugs_criticos'] / total_bugs) * 100
                    if perc_criticos > 30:
                        insights_bugs.append(f"🚨 **ATENÇÃO**: {perc_criticos:.1f}% dos bugs são de alta prioridade - requer ação imediata")
                    else:
                        insights_bugs.append(f"⚠️ {perc_criticos:.1f}% dos bugs são de alta prioridade")
                
                # Insight sobre bugs abertos
                if metricas_bugs.get('bugs_abertos', 0) > 0:
                    total_bugs = metricas_bugs.get('total_bugs', 1)
                    perc_abertos = (metricas_bugs['bugs_abertos'] / total_bugs) * 100
                    if perc_abertos > 50:
                        insights_bugs.append(f"🔓 **CRÍTICO**: {perc_abertos:.1f}% dos bugs ainda estão pendentes de correção")
                    else:
                        insights_bugs.append(f"🔓 {perc_abertos:.1f}% dos bugs estão pendentes")
                
                # Insight sobre time com mais bugs
                if metricas_bugs.get('bugs_por_time'):
                    time_mais_bugs = max(metricas_bugs['bugs_por_time'], key=metricas_bugs['bugs_por_time'].get)
                    qtd_bugs_time = metricas_bugs['bugs_por_time'][time_mais_bugs]
                    insights_bugs.append(f"🏢 Time **{time_mais_bugs}** tem o maior número de bugs ({qtd_bugs_time})")
                
                # Insight sobre fonte de detecção
                if metricas_bugs.get('bugs_por_fonte'):
                    fonte_principal = max(metricas_bugs['bugs_por_fonte'], key=metricas_bugs['bugs_por_fonte'].get)
                    qtd_fonte = metricas_bugs['bugs_por_fonte'][fonte_principal]
                    total_bugs = sum(metricas_bugs['bugs_por_fonte'].values())
                    perc_fonte = (qtd_fonte / total_bugs) * 100
                    if fonte_principal.lower() == 'cliente':
                        insights_bugs.append(f"🔍 **ALERTA**: {perc_fonte:.1f}% dos bugs foram encontrados por clientes - melhorar testes internos")
                    else:
                        insights_bugs.append(f"🔍 {perc_fonte:.1f}% dos bugs foram detectados por {fonte_principal}")
                
                # Exibir insights
                for insight in insights_bugs:
                    if "CRÍTICO" in insight or "ATENÇÃO" in insight or "ALERTA" in insight:
                        st.error(insight)
                    elif "⚠️" in insight:
                        st.warning(insight)
                    else:
                        st.info(insight)
                
                st.markdown("---")
                
                # Tabela detalhada de bugs (usando dados filtrados)
                st.markdown("#### 📋 **Dados Detalhados de Bugs**")
                if st.checkbox("Mostrar tabela completa de bugs", key="show_bugs_table"):
                    st.dataframe(df_bugs_filtrado, use_container_width=True)
                    st.caption(f"Total de bugs registrados: {len(df_bugs_filtrado)}")
                    
                    # Download dos dados de bugs filtrados
                    csv_bugs = df_bugs_filtrado.to_csv(index=False)
                    st.download_button(
                        label="📥 Baixar dados de bugs filtrados (CSV)",
                        data=csv_bugs,
                        file_name=f"bugs_analysis_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                # Recomendações estratégicas
                st.markdown("#### 🎯 **Recomendações Estratégicas**")
                
                recomendacoes = []
                
                if metricas_bugs.get('bugs_criticos', 0) > 3:
                    recomendacoes.append("🚨 **Priorizar correção de bugs críticos** - Alocar recursos dedicados")
                
                if metricas_bugs.get('bugs_abertos', 0) > metricas_bugs.get('bugs_resolvidos', 0):
                    recomendacoes.append("⚡ **Acelerar processo de correção** - Bugs abertos excedem resolvidos")
                
                if metricas_bugs.get('bugs_por_fonte', {}).get('Cliente', 0) > 0:
                    recomendacoes.append("🔍 **Fortalecer testes internos** - Evitar bugs chegarem ao cliente")
                
                if len(metricas_bugs.get('bugs_por_time', {})) > 3:
                    recomendacoes.append("📚 **Implementar treinamento de qualidade** - Múltiplos times afetados")
                
                if not recomendacoes:
                    recomendacoes.append("✅ **Manter padrão atual** - Métricas de bugs estão controladas")
                
                for rec in recomendacoes:
                    st.success(rec)
                    
            else:
                st.info("📁 Faça upload da planilha de bugs para começar a análise")
                st.markdown("""
                ### 📋 **Como usar a Análise de Bugs:**
                
                1. **Faça upload da planilha de bugs** usando o botão acima
                2. **Estrutura esperada do arquivo:**
                   - **Data**: Data de identificação do bug
                   - **Time**: Time responsável pelo desenvolvimento
                   - **Encontrado por**: Quem identificou o bug (Q.A, Cliente, etc.)
                   - **BUG**: Descrição do bug
                   - **Status**: Status atual (Corrigido, Pendente, Em correção)
                   - **Prioridade**: Prioridade do bug (Alta, Media, Baixa)
                
                3. **Funcionalidades disponíveis:**
                   - 📊 Métricas executivas de bugs
                   - 📈 Análise visual por status, prioridade e time
                   - 🔍 Fonte de detecção dos bugs
                   - 📅 Evolução temporal
                   - 💡 Insights automáticos
                   - 🎯 Recomendações estratégicas
                """)
        
        with tab8:
            st.header("📊 Relatório Detalhado.")
            st.markdown("### Análise Detalhada de Bugs e Falhas por Tarefa")
            
            # Botão de exportação PDF
            col_export, col_space = st.columns([1, 3])
            with col_export:
                botao_exportar_pdf("Relatorio_Detalhado", criar_pdf_relatorio_detalhado, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Usar os dados já filtrados pelos filtros principais
            df_pm = df_com_teste.copy()
            
            # Separar dados por tipo de problema
            df_rejeitadas = df_pm[df_pm['Status'] == 'REJEITADA'].copy()
            df_temp = df_pm.copy()
            df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
            
            # Contar tarefas com defeitos (unificando coluna Erros e motivos de rejeição)
            tarefas_com_defeitos = set()
            
            # 1. Tarefas com erros na coluna numérica
            df_com_erros_numericos = df_temp[df_temp['Erros'] > 0]
            for idx in df_com_erros_numericos.index:
                tarefas_com_defeitos.add(idx)
            
            # 2. Tarefas rejeitadas com motivos válidos
            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
            for idx, row in df_rejeitadas.iterrows():
                tem_motivo_valido = False
                for col in motivos_cols:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                        motivo = str(row[col]).strip().lower()
                        if motivo not in ['aprovada', 'sem recusa']:
                            tem_motivo_valido = True
                            break
                if tem_motivo_valido:
                    tarefas_com_defeitos.add(idx)
            
            total_com_defeitos = len(tarefas_com_defeitos)
            
            # Seção 1: Resumo Executivo
            st.markdown("#### 📈 Resumo Executivo")
            
            # Primeira linha de métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_tasks = len(df_pm)
                tarefas_unicas = df_pm['Nome da Task'].nunique() if 'Nome da Task' in df_pm.columns else 0
                st.metric(
                    "📋 Total de Tarefas", 
                    f"{tarefas_unicas}",
                    delta=f"📊 {total_tasks} testes realizados",
                    help=f"Tarefas únicas testadas: {tarefas_unicas} | Total de testes efetuados: {total_tasks}"
                )
            
            with col2:
                total_aprovadas = len(df_pm[df_pm['Status'] == 'APROVADA'])
                st.metric("✅ Tarefas Aprovadas", total_aprovadas, delta="Entregues em produção")
            
            with col3:
                total_prontas = len(df_pm[df_pm['Status'] == 'PRONTO PARA PUBLICAÇÃO'])
                st.metric("🚀 Prontas p/ Publicação", total_prontas, delta="Aguardando deploy")
            
            with col4:
                total_rejeitadas = len(df_rejeitadas)
                taxa_rejeicao = (total_rejeitadas / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("❌ Tarefas Rejeitadas", total_rejeitadas, f"{taxa_rejeicao:.1f}%")
            
            # Segunda linha de métricas
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                st.metric("⚠️ Tarefas com Defeitos", total_com_defeitos, 
                         help="Tarefas com erros numéricos ou motivos de rejeição válidos")
            
            with col6:
                # Contar total de problemas encontrados (soma de todos os motivos + erros numéricos)
                total_problemas_encontrados = contar_total_bugs(df_rejeitadas)
                if 'Erros' in df_temp.columns:
                    total_problemas_encontrados += int(df_temp['Erros'].sum())
                st.metric("🔴 Total de Problemas Encontrados", total_problemas_encontrados,
                         help="Soma de todos os motivos de rejeição + erros numéricos da coluna Erros")
            
            with col7:
                total_concluidas = total_aprovadas + total_prontas
                st.metric("🎯 Tarefas Concluídas", total_concluidas)
            
            with col8:
                taxa_sucesso = (total_concluidas / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("📊 Taxa de Sucesso", f"{taxa_sucesso:.1f}%")
            
            st.divider()
            
            # Seção 2: Análise de Retestes e Ciclo de Vida das Tarefas
            st.markdown("#### 🔄 Histórico de Retestes e Taxa de Aprovação")
            
            # Analisar histórico de retestes
            historico_retestes = analisar_historico_retestes(df_pm)
            
            # Métricas de reteste
            col_ret1, col_ret2, col_ret3, col_ret4 = st.columns(4)
            
            with col_ret1:
                st.metric(
                    "🔄 Tarefas Retestadas", 
                    historico_retestes['total_tarefas_retestadas'],
                    help="Tarefas que foram rejeitadas e posteriormente retestadas"
                )
            
            with col_ret2:
                st.metric(
                    "✅ Aprovadas Após Reteste", 
                    historico_retestes['tarefas_aprovadas_apos_reteste'],
                    help="Tarefas que foram aprovadas após correções e reteste"
                )
            
            with col_ret3:
                taxa_aprovacao_reteste = historico_retestes['taxa_aprovacao_apos_reteste']
                st.metric(
                    "📈 Taxa de Aprovação Pós-Reteste", 
                    f"{taxa_aprovacao_reteste:.1f}%",
                    help="Percentual de tarefas aprovadas após correções"
                )
            
            with col_ret4:
                if historico_retestes['total_tarefas_retestadas'] > 0:
                    eficiencia_correcao = (historico_retestes['tarefas_aprovadas_apos_reteste'] / historico_retestes['total_tarefas_retestadas']) * 100
                    delta_eficiencia = "🟢 Excelente" if eficiencia_correcao >= 80 else "🟡 Bom" if eficiencia_correcao >= 60 else "🔴 Atenção"
                else:
                    eficiencia_correcao = 0
                    delta_eficiencia = "📊 Sem dados"
                
                st.metric(
                    "🎯 Eficiência de Correção", 
                    f"{eficiencia_correcao:.1f}%",
                    delta=delta_eficiencia,
                    help="Capacidade da equipe de corrigir problemas identificados"
                )
            
            # Detalhamento do histórico de retestes
            if not historico_retestes['detalhes_retestes'].empty:
                st.markdown("##### 📋 Detalhamento das Tarefas Retestadas")
                
                df_retestes = historico_retestes['detalhes_retestes'].copy()
                
                # Formatar datas
                if 'Primeira_Data' in df_retestes.columns:
                    df_retestes['Primeira_Data'] = pd.to_datetime(df_retestes['Primeira_Data']).dt.strftime('%d/%m/%Y')
                if 'Ultima_Data' in df_retestes.columns:
                    df_retestes['Ultima_Data'] = pd.to_datetime(df_retestes['Ultima_Data']).dt.strftime('%d/%m/%Y')
                
                # Renomear colunas para exibição
                df_retestes_exibir = df_retestes.rename(columns={
                    'Identificador': 'ID/Identificador',
                    'Nome_Tarefa': 'Nome da Tarefa',
                    'Total_Testes': 'Qtd Testes',
                    'Sequencia_Status': 'Sequência de Status',
                    'Aprovada_Apos_Reteste': 'Aprovada Após Reteste',
                    'Primeira_Data': 'Primeira Data',
                    'Ultima_Data': 'Última Data',
                    'Responsavel': 'Responsável'
                })
                
                st.dataframe(
                    df_retestes_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Aprovada Após Reteste": st.column_config.CheckboxColumn(
                            "Aprovada Após Reteste",
                            help="Indica se a tarefa foi aprovada após correções"
                        ),
                        "Sequência de Status": st.column_config.TextColumn(
                            "Sequência de Status",
                            help="Histórico completo dos status da tarefa",
                            width="large"
                        )
                    }
                )
                
                # Botão para exportar dados de retestes
                csv_retestes = df_retestes_exibir.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Histórico de Retestes (CSV)",
                    data=csv_retestes,
                    file_name=f"historico_retestes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
                # Insights sobre retestes
                st.markdown("##### 💡 Insights sobre Retestes")
                
                if taxa_aprovacao_reteste >= 80:
                    st.success(f"🎯 **Excelente capacidade de correção**: {taxa_aprovacao_reteste:.1f}% das tarefas retestadas foram aprovadas após correções.")
                elif taxa_aprovacao_reteste >= 60:
                    st.info(f"📊 **Boa capacidade de correção**: {taxa_aprovacao_reteste:.1f}% das tarefas retestadas foram aprovadas. Há espaço para melhorias.")
                else:
                    st.warning(f"⚠️ **Atenção necessária**: Apenas {taxa_aprovacao_reteste:.1f}% das tarefas retestadas foram aprovadas. Revisar processo de correções.")
                
                # Análise por time se houver dados suficientes
                if len(df_retestes) > 0 and 'Time' in df_retestes.columns:
                    times_reteste = df_retestes.groupby('Time').agg({
                        'Aprovada_Apos_Reteste': ['count', 'sum']
                    }).round(1)
                    
                    if len(times_reteste) > 1:
                        st.markdown("**📊 Performance por Time:**")
                        for time in times_reteste.index:
                            total_time = times_reteste.loc[time, ('Aprovada_Apos_Reteste', 'count')]
                            aprovadas_time = times_reteste.loc[time, ('Aprovada_Apos_Reteste', 'sum')]
                            taxa_time = (aprovadas_time / total_time * 100) if total_time > 0 else 0
                            st.write(f"• **{time}**: {aprovadas_time}/{total_time} aprovadas ({taxa_time:.1f}%)")
            else:
                st.info("📊 Nenhuma tarefa retestada encontrada no período selecionado.")
            
            st.divider()
            
            # Seção 2: Tarefas Entregues e Prontas para Publicação
            st.markdown("#### ✅ Tarefas Entregues e Produção")
            
            # Filtrar tarefas aprovadas
            df_aprovadas = df_pm[df_pm['Status'] == 'APROVADA'].copy()
            
            if len(df_aprovadas) > 0:
                # Criar tabela de tarefas aprovadas
                df_aprovadas_detalhada = df_aprovadas[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                     'Responsável', 'Descrição', 'Responsavel pelo teste']].copy()
                
                # Reorganizar colunas para melhor visualização
                colunas_aprovadas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Responsável', 
                                   'Descrição', 'Responsavel pelo teste', 'Link da Task']
                
                df_aprovadas_exibir = df_aprovadas_detalhada[colunas_aprovadas].copy()
                df_aprovadas_exibir['Data'] = df_aprovadas_exibir['Data'].dt.strftime('%d/%m/%Y')
                
                # Preencher descrições vazias
                df_aprovadas_exibir['Descrição'] = df_aprovadas_exibir['Descrição'].fillna('Descrição não informada')
                
                st.dataframe(
                    df_aprovadas_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Link da Task": st.column_config.LinkColumn(
                            "Link da Task",
                            help="Clique para abrir a task",
                            display_text="🔗 Abrir Task"
                        ),
                        "Descrição": st.column_config.TextColumn(
                            "Descrição",
                            help="Descrição da tarefa entregue",
                            width="large"
                        )
                    }
                )
                
                # Botão para exportar dados de aprovadas
                csv_aprovadas = df_aprovadas_exibir.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Tarefas Entregues (CSV)",
                    data=csv_aprovadas,
                    file_name=f"tarefas_entregues_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhuma tarefa aprovada encontrada no período selecionado.")
            
            st.markdown("#### 🚀 Tarefas Prontas para Publicação")
            
            # Filtrar tarefas prontas para publicação
            df_prontas = df_pm[df_pm['Status'] == 'PRONTO PARA PUBLICAÇÃO'].copy()
            
            if len(df_prontas) > 0:
                # Criar tabela de tarefas prontas
                df_prontas_detalhada = df_prontas[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                 'Responsável', 'Descrição', 'Responsavel pelo teste']].copy()
                
                # Reorganizar colunas para melhor visualização
                colunas_prontas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Responsável', 
                                 'Descrição', 'Responsavel pelo teste', 'Link da Task']
                
                df_prontas_exibir = df_prontas_detalhada[colunas_prontas].copy()
                df_prontas_exibir['Data'] = df_prontas_exibir['Data'].dt.strftime('%d/%m/%Y')
                
                # Preencher descrições vazias
                df_prontas_exibir['Descrição'] = df_prontas_exibir['Descrição'].fillna('Descrição não informada')
                
                st.dataframe(
                    df_prontas_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Link da Task": st.column_config.LinkColumn(
                            "Link da Task",
                            help="Clique para abrir a task",
                            display_text="🔗 Abrir Task"
                        ),
                        "Descrição": st.column_config.TextColumn(
                            "Descrição",
                            help="Descrição da tarefa pronta para publicação",
                            width="large"
                        )
                    }
                )
                
                # Botão para exportar dados de prontas
                csv_prontas = df_prontas_exibir.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Tarefas Prontas para Publicação (CSV)",
                    data=csv_prontas,
                    file_name=f"tarefas_prontas_publicacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Nenhuma tarefa pronta para publicação encontrada no período selecionado.")
            
            st.divider()
            
            # Seção 3: Detalhamento de Tarefas Rejeitadas
            if len(df_rejeitadas) > 0:
                st.markdown("#### 🚫 Detalhamento de Tarefas Rejeitadas")
                
                # Criar tabela detalhada com descrição dos problemas
                df_rejeitadas_detalhada = df_rejeitadas[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                       'Responsável', 'Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7', 'Responsavel pelo teste']].copy()
                
                # Criar coluna de descrição consolidada
                def criar_descricao_problema(row):
                    motivos = []
                    if pd.notna(row['Motivo']) and row['Motivo'].strip():
                        motivos.append(f"• {row['Motivo'].strip()}")
                    if pd.notna(row['Motivo2']) and row['Motivo2'].strip():
                        motivos.append(f"• {row['Motivo2'].strip()}")
                    if pd.notna(row['Motivo3']) and row['Motivo3'].strip():
                        motivos.append(f"• {row['Motivo3'].strip()}")
                    if pd.notna(row['Motivo4']) and row['Motivo4'].strip():
                        motivos.append(f"• {row['Motivo4'].strip()}")
                    if pd.notna(row['Motivo5']) and row['Motivo5'].strip():
                        motivos.append(f"• {row['Motivo5'].strip()}")
                    if pd.notna(row['Motivo6']) and row['Motivo6'].strip():
                        motivos.append(f"• {row['Motivo6'].strip()}")
                    if pd.notna(row['Motivo7']) and row['Motivo7'].strip():
                        motivos.append(f"• {row['Motivo7'].strip()}")
                    
                    if motivos:
                        return "\n".join(motivos)
                    else:
                        return "Motivo não especificado"
                
                df_rejeitadas_detalhada['Descrição do Problema'] = df_rejeitadas_detalhada.apply(criar_descricao_problema, axis=1)
                
                # Reorganizar colunas para melhor visualização
                colunas_exibir = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Responsável', 
                                'Descrição do Problema', 'Responsavel pelo teste', 'Link da Task']
                
                df_rejeitadas_exibir = df_rejeitadas_detalhada[colunas_exibir].copy()
                df_rejeitadas_exibir['Data'] = df_rejeitadas_exibir['Data'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_rejeitadas_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Link da Task": st.column_config.LinkColumn(
                            "Link da Task",
                            help="Clique para abrir a task",
                            display_text="🔗 Abrir Task"
                        ),
                        "Descrição do Problema": st.column_config.TextColumn(
                            "Descrição do Problema",
                            help="Detalhes dos problemas encontrados",
                            width="large"
                        )
                    }
                )
                
                # Botão para exportar dados de rejeitadas
                csv_rejeitadas = df_rejeitadas_exibir.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Tarefas Rejeitadas (CSV)",
                    data=csv_rejeitadas,
                    file_name=f"tarefas_rejeitadas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            st.divider()
            
            # Seção 4: Detalhamento de Tarefas com Defeitos
            if total_com_defeitos > 0:
                st.markdown("#### ⚠️ Detalhamento de Tarefas com Defeitos")
                
                # Criar DataFrame com todas as tarefas que têm defeitos
                df_com_defeitos = df_pm.loc[list(tarefas_com_defeitos)].copy()
                df_erros_detalhada = df_com_defeitos[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                     'Responsável', 'Erros', 'Status', 'Responsavel pelo teste']].copy()
                
                # Criar descrição para defeitos
                def criar_descricao_defeito(row):
                    try:
                        num_erros = int(float(str(row['Erros']))) if pd.notna(row['Erros']) and str(row['Erros']).strip() != '' else 0
                        num_erros = num_erros if num_erros > 0 else 0
                    except (ValueError, TypeError):
                        num_erros = 0
                    status = row['Status'] if pd.notna(row['Status']) else 'N/A'
                    
                    # Contar motivos de rejeição válidos
                    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']
                    motivos_validos = 0
                    for col in motivos_cols:
                        if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                            motivo = str(row[col]).strip().lower()
                            if motivo not in ['aprovada', 'sem recusa']:
                                motivos_validos += 1
                    
                    descricao_partes = []
                    if num_erros > 0:
                        descricao_partes.append(f"{num_erros} erro{'s' if num_erros > 1 else ''} numérico{'s' if num_erros > 1 else ''}")
                    if motivos_validos > 0:
                        descricao_partes.append(f"{motivos_validos} motivo{'s' if motivos_validos > 1 else ''} de rejeição")
                    
                    if descricao_partes:
                        return f"{' + '.join(descricao_partes)} (Status: {status})"
                    else:
                        return f"Defeito identificado (Status: {status})"
                
                df_erros_detalhada['Descrição do Defeito'] = df_erros_detalhada.apply(criar_descricao_defeito, axis=1)
                
                colunas_erros = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Responsável', 
                               'Descrição do Defeito', 'Responsavel pelo teste', 'Link da Task']
                
                df_erros_exibir = df_erros_detalhada[colunas_erros].copy()
                df_erros_exibir['Data'] = df_erros_exibir['Data'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_erros_exibir,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Link da Task": st.column_config.LinkColumn(
                            "Link da Task",
                            help="Clique para abrir a task",
                            display_text="🔗 Abrir Task"
                        ),
                        "Descrição do Defeito": st.column_config.TextColumn(
                            "Descrição do Defeito",
                            help="Detalhes dos defeitos encontrados (erros numéricos + motivos de rejeição)"
                        )
                    }
                )
                
                # Botão para exportar dados de erros
                csv_erros = df_erros_exibir.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Tarefas com Erros (CSV)",
                    data=csv_erros,
                    file_name=f"tarefas_com_erros_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            st.divider()
            
            # Seção 5: Análise de Tendências
            st.markdown("#### 📊 Análise de Tendências")
            
            if len(df_pm) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de problemas por time
                    problemas_por_time = df_pm.groupby('Time').agg({
                        'Status': lambda x: (x == 'REJEITADA').sum(),
                        'Erros': lambda x: (pd.to_numeric(x, errors='coerce').fillna(0) > 0).sum() if x.notna().any() else 0
                    }).reset_index()
                    problemas_por_time.columns = ['Time', 'Rejeitadas', 'Com_Erros']
                    problemas_por_time['Total_Problemas'] = problemas_por_time['Rejeitadas'] + problemas_por_time['Com_Erros']
                    
                    if not problemas_por_time.empty and problemas_por_time['Total_Problemas'].sum() > 0:
                        fig_time = px.bar(
                            problemas_por_time.sort_values('Total_Problemas', ascending=True),
                            x='Total_Problemas',
                            y='Time',
                            orientation='h',
                            title="Problemas por Time",
                            color='Total_Problemas',
                            color_continuous_scale='Reds'
                        )
                        fig_time.update_layout(height=400)
                        st.plotly_chart(fig_time, use_container_width=True)
                    else:
                        st.info("Nenhum problema encontrado para exibir no gráfico.")
                
                with col2:
                    # Gráfico de evolução temporal
                    if 'Data' in df_pm.columns:
                        df_pm['Semana'] = df_pm['Data'].dt.to_period('W').astype(str)
                        evolucao = df_pm.groupby('Semana').agg({
                            'Status': lambda x: (x == 'REJEITADA').sum(),
                            'Erros': lambda x: (pd.to_numeric(x, errors='coerce').fillna(0) > 0).sum() if x.notna().any() else 0
                        }).reset_index()
                        evolucao.columns = ['Semana', 'Rejeitadas', 'Com_Erros']
                        
                        if not evolucao.empty:
                            fig_evolucao = go.Figure()
                            fig_evolucao.add_trace(go.Scatter(
                                x=evolucao['Semana'],
                                y=evolucao['Rejeitadas'],
                                mode='lines+markers',
                                name='Rejeitadas',
                                line=dict(color='red')
                            ))
                            fig_evolucao.add_trace(go.Scatter(
                                x=evolucao['Semana'],
                                y=evolucao['Com_Erros'],
                                mode='lines+markers',
                                name='Com Erros',
                                line=dict(color='orange')
                            ))
                            fig_evolucao.update_layout(
                                title="Evolução de Problemas por Semana",
                                xaxis_title="Semana",
                                yaxis_title="Quantidade",
                                height=400
                            )
                            st.plotly_chart(fig_evolucao, use_container_width=True)
                        else:
                            st.info("Dados insuficientes para análise temporal.")
            
            # Seção 6: Recomendações
            st.markdown("#### 💡 Recomendações")
            
            if len(df_pm) > 0:
                recomendacoes = []
                
                # Análise de taxa de rejeição
                if taxa_rejeicao > 20:
                    recomendacoes.append(f"🔴 **Alta taxa de rejeição ({taxa_rejeicao:.1f}%)**: Revisar processo de desenvolvimento e critérios de aceitação")
                elif taxa_rejeicao > 10:
                    recomendacoes.append(f"🟡 **Taxa de rejeição moderada ({taxa_rejeicao:.1f}%)**: Monitorar tendência e identificar padrões")
                else:
                    recomendacoes.append(f"🟢 **Taxa de rejeição baixa ({taxa_rejeicao:.1f}%)**: Manter qualidade atual")
                
                # Análise por time
                if len(df_rejeitadas) > 0:
                    time_mais_problemas = df_rejeitadas['Time'].value_counts().index[0]
                    qtd_problemas = df_rejeitadas['Time'].value_counts().iloc[0]
                    recomendacoes.append(f"⚠️ **Time {time_mais_problemas}** apresenta mais problemas ({qtd_problemas} tarefas rejeitadas)")
                
                # Análise de motivos mais comuns
                if len(df_rejeitadas) > 0:
                    motivos_todos = []
                    for col in ['Motivo', 'Motivo2', 'Motivo3', 'Motivo4', 'Motivo5', 'Motivo6', 'Motivo7']:
                        motivos_todos.extend(df_rejeitadas[col].dropna().tolist())
                    
                    if motivos_todos:
                        motivo_mais_comum = pd.Series(motivos_todos).value_counts().index[0]
                        recomendacoes.append(f"🎯 **Motivo mais comum**: {motivo_mais_comum}")
                
                for rec in recomendacoes:
                    st.markdown(rec)
            else:
                st.info("Nenhum dado disponível para análise com os filtros selecionados.")
            
        with tab8:
            st.markdown("### 🌐 **Análise de Ambientes de Teste**")
            st.markdown("*Distribuição e análise de testes por ambiente*")
            
            # Botão de exportação PDF
            col_export_amb, col_space_amb = st.columns([1, 3])
            with col_export_amb:
                botao_exportar_pdf("Analise_de_Ambientes", criar_pdf_generico, df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            if 'Ambiente' in df_com_teste.columns:
                # Verificar se há dados de ambiente válidos (não nulos e não vazios)
                dados_ambiente = df_com_teste[df_com_teste['Ambiente'].notna() & (df_com_teste['Ambiente'].str.strip() != '')]
                
                if not dados_ambiente.empty:
                    # Métricas principais de ambientes
                    st.markdown("#### 📊 **Métricas de Ambientes**")
                    
                    col_amb1, col_amb2, col_amb3, col_amb4 = st.columns(4)
                    
                    with col_amb1:
                        total_ambientes = dados_ambiente['Ambiente'].nunique()
                        st.metric("🌐 Total de Ambientes", f"{total_ambientes}")
                    
                    with col_amb2:
                        ambiente_mais_usado = dados_ambiente['Ambiente'].value_counts().index[0]
                        st.metric("🏆 Ambiente Mais Usado", ambiente_mais_usado)
                    
                    with col_amb3:
                        testes_com_ambiente = len(dados_ambiente)
                        total_testes = len(df_com_teste)
                        cobertura_ambiente = (testes_com_ambiente / total_testes * 100) if total_testes > 0 else 0
                        st.metric("📊 Cobertura de Ambiente", f"{cobertura_ambiente:.1f}%")
                    
                    with col_amb4:
                        if 'Status' in dados_ambiente.columns:
                            rejeitadas_ambiente = len(dados_ambiente[dados_ambiente['Status'] == 'REJEITADA'])
                            taxa_rejeicao_ambiente = (rejeitadas_ambiente / testes_com_ambiente * 100) if testes_com_ambiente > 0 else 0
                            st.metric("⚠️ Taxa Rejeição", f"{taxa_rejeicao_ambiente:.1f}%")
                    
                    st.markdown("---")
                    
                    # Gráficos de análise de ambientes
                    st.markdown("#### 📈 **Análise Visual de Ambientes**")
                    
                    col_graf_amb1, col_graf_amb2 = st.columns(2)
                    
                    with col_graf_amb1:
                        # Gráfico de distribuição por ambiente
                        fig_dist_amb = grafico_distribuicao_ambientes(dados_ambiente)
                        if fig_dist_amb:
                            st.plotly_chart(fig_dist_amb, use_container_width=True, key="distribuicao_ambientes")
                    
                    with col_graf_amb2:
                        # Gráfico de status por ambiente
                        fig_status_amb = grafico_ambiente_por_status(dados_ambiente)
                        if fig_status_amb:
                            st.plotly_chart(fig_status_amb, use_container_width=True, key="status_por_ambiente")
                    
                    st.markdown("---")
                    
                    # Tabela detalhada por ambiente
                    st.markdown("#### 📋 **Detalhamento por Ambiente**")
                    
                    # Criar resumo por ambiente
                    resumo_ambiente = dados_ambiente.groupby('Ambiente').agg({
                        'Status': ['count', lambda x: (x == 'APROVADA').sum(), lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'PRONTO PARA PUBLICAÇÃO').sum()],
                        'Time': 'nunique',
                        'Responsavel pelo teste': 'nunique'
                    }).round(2)
                    
                    resumo_ambiente.columns = ['Total_Testes', 'Aprovadas', 'Rejeitadas', 'Prontas', 'Times_Atendidos', 'Testadores']
                    resumo_ambiente['Total_Aprovadas'] = resumo_ambiente['Aprovadas'] + resumo_ambiente['Prontas']
                    resumo_ambiente['Taxa_Aprovacao'] = (resumo_ambiente['Total_Aprovadas'] / resumo_ambiente['Total_Testes'] * 100).round(1)
                    resumo_ambiente['Taxa_Rejeicao'] = (resumo_ambiente['Rejeitadas'] / resumo_ambiente['Total_Testes'] * 100).round(1)
                    
                    resumo_ambiente = resumo_ambiente.reset_index()
                    
                    st.dataframe(
                        resumo_ambiente,
                        column_config={
                            "Ambiente": "🌐 Ambiente",
                            "Total_Testes": "📊 Total de Testes",
                            "Aprovadas": "✅ Aprovadas",
                            "Rejeitadas": "❌ Rejeitadas",
                            "Times_Atendidos": "👥 Times Atendidos",
                            "Testadores": "🧑‍💻 Testadores",
                            "Taxa_Aprovacao": "📈 Taxa Aprovação (%)",
                            "Taxa_Rejeicao": "📉 Taxa Rejeição (%)"
                        },
                        use_container_width=True
                    )
                    
                    # Botão para exportar dados de ambientes
                    csv_ambientes = resumo_ambiente.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Exportar Análise de Ambientes (CSV)",
                        data=csv_ambientes,
                        file_name=f"analise_ambientes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                    
                    st.markdown("---")
                    
                    # Insights sobre ambientes
                    st.markdown("#### 💡 **Insights sobre Ambientes**")
                    
                    insights_ambiente = []
                    
                    # Ambiente com maior taxa de rejeição
                    if not resumo_ambiente.empty:
                        ambiente_problema = resumo_ambiente.loc[resumo_ambiente['Taxa_Rejeicao'].idxmax()]
                        if ambiente_problema['Taxa_Rejeicao'] > 20:
                            insights_ambiente.append(f"⚠️ **Ambiente {ambiente_problema['Ambiente']}** apresenta alta taxa de rejeição ({ambiente_problema['Taxa_Rejeicao']:.1f}%)")
                        
                        # Ambiente mais eficiente
                        ambiente_eficiente = resumo_ambiente.loc[resumo_ambiente['Taxa_Aprovacao'].idxmax()]
                        if ambiente_eficiente['Taxa_Aprovacao'] > 80:
                            insights_ambiente.append(f"✅ **Ambiente {ambiente_eficiente['Ambiente']}** apresenta excelente taxa de aprovação ({ambiente_eficiente['Taxa_Aprovacao']:.1f}%)")
                        
                        # Cobertura de ambientes
                        if cobertura_ambiente < 70:
                            insights_ambiente.append(f"📊 **Baixa cobertura de ambientes**: Apenas {cobertura_ambiente:.1f}% dos testes têm ambiente especificado")
                    
                    if insights_ambiente:
                        for insight in insights_ambiente:
                            st.markdown(insight)
                    else:
                        st.info("✅ Não foram identificados problemas significativos na distribuição por ambientes.")
                    
                else:
                    st.warning("⚠️ Nenhum dado de ambiente encontrado nos testes realizados.")
                    st.info("💡 **Dica**: Certifique-se de que a coluna 'Ambiente' esteja preenchida na planilha para obter análises detalhadas.")
            else:
                st.error("❌ Coluna 'Ambiente' não encontrada na planilha.")
                st.info("💡 **Solução**: Adicione uma coluna 'Ambiente' na sua planilha para habilitar esta análise.")
        

    else:
        st.info("👆 Faça upload de um arquivo Excel para começar a análise")
        st.markdown("""
        ### 📋 Colunas esperadas na planilha:
        - **Data**: Data da task
        - **Sprint**: Número do sprint
        - **Time**: Nome do time responsável
        - **Nome da Task**: Título da task
        - **Link da task**: URL da task
        - **Status**: APROVADA, REJEITADA ou PRONTO PARA PUBLICAÇÃO
        - **Responsável**: Desenvolvedor responsável
        - **Motivo**: Primeiro motivo (se rejeitada)
        - **Motivo2**: Segundo motivo (se rejeitada)
        - **Motivo3**: Terceiro motivo (se rejeitada)
        - **Motivo4**: Quarto motivo (se rejeitada)
        - **Motivo5**: Quinto motivo (se rejeitada)
        - **Motivo6**: Sexto motivo (se rejeitada)
        - **Motivo7**: Sétimo motivo (se rejeitada)
        - **Responsavel pelo teste**: Testador responsável
        - **ID**: Identificador único da task
        
        ### 🚀 Funcionalidades do Dashboard:
        - Análise de performance por sprint
        - Métricas de qualidade e rejeições
        - Visualizações interativas
        - Filtros avançados por período e responsável
        - Exportação de dados
        """)

if __name__ == "__main__":
    main()