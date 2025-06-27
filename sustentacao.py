import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import io

def carregar_dados_sustentacao():
    """
    Função para carregar dados das planilhas de sustentação
    """
    uploaded_files = st.file_uploader(
        "Faça upload das planilhas de sustentação",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Selecione as planilhas: 'Planilha sem título.xlsx' (velocidade) e 'Planilha horas por dev.xlsx' (tarefas)"
    )
    
    dados = {}
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                if "sem título" in uploaded_file.name.lower() or "velocidade" in uploaded_file.name.lower():
                    # Planilha de velocidade
                    df = pd.read_excel(uploaded_file)
                    dados['velocidade'] = df
                    st.success(f"✅ Planilha de velocidade carregada: {uploaded_file.name}")
                    
                elif "horas" in uploaded_file.name.lower() or "dev" in uploaded_file.name.lower():
                    # Planilha de tarefas/horas
                    df = pd.read_excel(uploaded_file)
                    dados['tarefas'] = df
                    st.success(f"✅ Planilha de tarefas carregada: {uploaded_file.name}")
                    
                else:
                    # Tentar identificar pela estrutura
                    df = pd.read_excel(uploaded_file)
                    if 'Velocidade Planejada' in df.columns and 'Velocidade Real' in df.columns:
                        dados['velocidade'] = df
                        st.success(f"✅ Planilha de velocidade identificada: {uploaded_file.name}")
                    elif 'Tarefa' in df.columns and 'Responsável' in df.columns:
                        dados['tarefas'] = df
                        st.success(f"✅ Planilha de tarefas identificada: {uploaded_file.name}")
                    else:
                        st.warning(f"⚠️ Estrutura não reconhecida: {uploaded_file.name}")
                        
            except Exception as e:
                st.error(f"❌ Erro ao carregar {uploaded_file.name}: {str(e)}")
    
    return dados

def processar_dados_sustentacao(dados):
    """
    Processa e limpa os dados de sustentação
    """
    dados_processados = {}
    
    # Processar dados de velocidade
    if 'velocidade' in dados:
        df_vel = dados['velocidade'].copy()
        # Limpar dados
        df_vel = df_vel.dropna(subset=['Sprint'])
        df_vel['Sprint'] = df_vel['Sprint'].astype(str)
        
        # Calcular diferença (Real - Planejada)
        if 'Velocidade Real' in df_vel.columns and 'Velocidade Planejada' in df_vel.columns:
            df_vel['Diff'] = df_vel['Velocidade Real'] - df_vel['Velocidade Planejada']
        
        dados_processados['velocidade'] = df_vel
    
    # Processar dados de tarefas
    if 'tarefas' in dados:
        df_tarefas = dados['tarefas'].copy()
        
        # Limpar dados
        df_tarefas = df_tarefas.dropna(subset=['Tarefa'])
        
        # Processar datas
        for col in ['Inicio da tarefa', 'Finalização da tarefa']:
            if col in df_tarefas.columns:
                df_tarefas[col] = pd.to_datetime(df_tarefas[col], errors='coerce')
        
        # Processar horas
        for col in ['Horas estimadas', 'Horas trabalhadas']:
            if col in df_tarefas.columns:
                df_tarefas[col] = pd.to_numeric(df_tarefas[col], errors='coerce')
        
        # Calcular desvio de horas
        if 'Horas estimadas' in df_tarefas.columns and 'Horas trabalhadas' in df_tarefas.columns:
            df_tarefas['Desvio Horas'] = df_tarefas['Horas trabalhadas'] - df_tarefas['Horas estimadas']
            df_tarefas['Desvio Percentual'] = ((df_tarefas['Horas trabalhadas'] - df_tarefas['Horas estimadas']) / df_tarefas['Horas estimadas'] * 100).round(2)
        
        dados_processados['tarefas'] = df_tarefas
    
    return dados_processados

def grafico_velocidade_sprint(df_velocidade):
    """
    Gráfico de velocidade planejada vs real por sprint com explicações sobre story points
    """
    st.markdown("""
    ### 📈 Análise de Velocidade - Story Points
    
    **Story Points** representam a complexidade e esforço estimado para completar as tarefas do time.
    Este gráfico compara:
    - **Velocidade Planejada**: Quantidade de story points que o time se comprometeu a entregar
    - **Velocidade Real**: Quantidade de story points efetivamente entregues
    
    💡 **Como interpretar:**
    - Linha verde acima da azul = Time superou expectativas
    - Linha verde abaixo da azul = Time não atingiu o planejado
    - Linhas próximas = Boa previsibilidade do time
    """)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_velocidade['Sprint'],
        y=df_velocidade['Velocidade Planejada'],
        mode='lines+markers',
        name='📋 Story Points Planejados',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=10, symbol='diamond'),
        hovertemplate='<b>Sprint %{x}</b><br>Planejado: %{y} story points<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_velocidade['Sprint'],
        y=df_velocidade['Velocidade Real'],
        mode='lines+markers',
        name='✅ Story Points Entregues',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=10, symbol='circle'),
        hovertemplate='<b>Sprint %{x}</b><br>Entregue: %{y} story points<extra></extra>'
    ))
    
    # Adicionar área entre as linhas para mostrar diferença
    fig.add_trace(go.Scatter(
        x=df_velocidade['Sprint'].tolist() + df_velocidade['Sprint'].tolist()[::-1],
        y=df_velocidade['Velocidade Planejada'].tolist() + df_velocidade['Velocidade Real'].tolist()[::-1],
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Diferença',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title={
            'text': '📊 Evolução da Velocidade do Time - Story Points por Sprint',
            'x': 0.5,
            'font': {'size': 16}
        },
        xaxis_title='Sprint',
        yaxis_title='Story Points',
        hovermode='x unified',
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        annotations=[
            dict(
                text="Story Points medem complexidade e esforço das tarefas",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                xanchor='center',
                font=dict(size=10, color="gray")
            )
        ]
    )
    
    return fig

def grafico_desvio_velocidade(df_velocidade):
    """
    Gráfico de desvio da velocidade com explicações detalhadas
    """
    st.markdown("""
    ### 📊 Análise de Desvios - Performance vs Planejamento
    
    Este gráfico mostra a **diferença entre story points planejados e entregues** em cada sprint:
    
    🔴 **Barras Vermelhas (Muito abaixo)**: Time entregou **muito menos** story points que o planejado (diferença > 2)
    🟠 **Barras Laranjas (Abaixo)**: Time entregou **menos** story points que o planejado (diferença < 2)
    🟢 **Barras Verdes (Positivas)**: Time entregou **igual ou mais** story points que o planejado
    🔵 **Barras Azuis (Muito acima)**: Time **superou muito** as expectativas (diferença > 2)
    
    💡 **Insights importantes:**
    - Desvios consistentemente negativos podem indicar superestimação ou impedimentos
    - Desvios consistentemente positivos podem indicar subestimação ou melhoria de processo
    - Variação alta indica instabilidade na previsibilidade
    """)
    
    # Calcular cores baseadas no valor
    colors = []
    for diff in df_velocidade['Diff']:
        if diff < -2:
            colors.append('#d62728')  # Vermelho forte
        elif diff < 0:
            colors.append('#ff7f0e')  # Laranja
        elif diff == 0:
            colors.append('#2ca02c')  # Verde
        elif diff <= 2:
            colors.append('#2ca02c')  # Verde
        else:
            colors.append('#1f77b4')  # Azul (superou muito)
    
    fig = go.Figure(data=[
        go.Bar(
            x=df_velocidade['Sprint'],
            y=df_velocidade['Diff'],
            marker_color=colors,
            text=[f"{diff:+.0f}" for diff in df_velocidade['Diff']],
            textposition='outside',
            hovertemplate='<b>Sprint %{x}</b><br>Desvio: %{y:+.0f} story points<br>%{customdata}<extra></extra>',
            customdata=[f"{'Superou' if diff > 0 else 'Abaixo' if diff < 0 else 'Exato'}" for diff in df_velocidade['Diff']]
        )
    ])
    
    # Adicionar linha de referência no zero
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="black",
        annotation_text="Meta: Zero desvio",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title={
            'text': '📈 Desvio de Performance - Story Points (Real - Planejado)',
            'x': 0.5,
            'font': {'size': 16}
        },
        xaxis_title='Sprint',
        yaxis_title='Desvio em Story Points',
        height=450,
        showlegend=True,
        annotations=[
            dict(
                text="Valores positivos = Superou expectativas | Valores negativos = Abaixo do planejado",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                xanchor='center',
                font=dict(size=10, color="gray")
            )
        ]
    )
    
    return fig

def grafico_horas_por_dev(df_tarefas):
    """
    Gráfico de horas trabalhadas por desenvolvedor
    """
    if 'Responsável' not in df_tarefas.columns or 'Horas trabalhadas' not in df_tarefas.columns:
        return None
    
    horas_dev = df_tarefas.groupby('Responsável')['Horas trabalhadas'].sum().reset_index()
    horas_dev = horas_dev.sort_values('Horas trabalhadas', ascending=True)
    
    fig = px.bar(
        horas_dev,
        x='Horas trabalhadas',
        y='Responsável',
        orientation='h',
        title='Total de Horas Trabalhadas por Desenvolvedor',
        color='Horas trabalhadas',
        color_continuous_scale='Blues',
        text='Horas trabalhadas'
    )
    
    fig.update_traces(
        texttemplate='%{text:.1f}h',
        textposition='outside'
    )
    
    fig.update_layout(height=400)
    return fig

def grafico_comparativo_horas(df_tarefas):
    """
    Gráfico de barras comparativo entre horas estimadas e trabalhadas por desenvolvedor
    """
    if 'Horas estimadas' not in df_tarefas.columns or 'Horas trabalhadas' not in df_tarefas.columns or 'Responsável' not in df_tarefas.columns:
        return None
    
    df_com_horas = df_tarefas.dropna(subset=['Horas estimadas', 'Horas trabalhadas', 'Responsável'])
    
    # Agrupar por desenvolvedor
    df_agrupado = df_com_horas.groupby('Responsável').agg({
        'Horas estimadas': 'sum',
        'Horas trabalhadas': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    
    # Barras de horas estimadas
    fig.add_trace(go.Bar(
        name='📋 Horas Estimadas',
        x=df_agrupado['Responsável'],
        y=df_agrupado['Horas estimadas'],
        marker_color='#3498db',
        text=[f'{val:.1f}h' for val in df_agrupado['Horas estimadas']],
        textposition='outside',
        textfont=dict(size=10, color='#3498db'),
        hovertemplate='<b>%{x}</b><br>Estimado: %{y} horas<extra></extra>'
    ))
    
    # Barras de horas trabalhadas
    fig.add_trace(go.Bar(
        name='⏱️ Horas Trabalhadas',
        x=df_agrupado['Responsável'],
        y=df_agrupado['Horas trabalhadas'],
        marker_color='#27ae60',
        text=[f'{val:.1f}h' for val in df_agrupado['Horas trabalhadas']],
        textposition='outside',
        textfont=dict(size=10, color='#27ae60'),
        hovertemplate='<b>%{x}</b><br>Trabalhado: %{y} horas<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': '📊 Comparação: Horas Estimadas vs Trabalhadas por Desenvolvedor',
            'x': 0.5,
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title='Desenvolvedores',
        yaxis_title='Horas',
        barmode='group',
        height=550,
        margin=dict(t=100, b=120, l=60, r=60),
        xaxis={
            'tickfont': {'size': 11}
        },
        yaxis={
            'tickfont': {'size': 11}
        },
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font={'size': 12}
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Adicionar grid sutil
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_xaxes(showgrid=False)
    
    return fig

def grafico_desvio_percentual(df_tarefas):
    """
    Gráfico de desvio percentual por desenvolvedor
    """
    if 'Desvio Percentual' not in df_tarefas.columns:
        return None
    
    df_desvios = df_tarefas.dropna(subset=['Desvio Percentual', 'Responsável'])
    desvio_por_dev = df_desvios.groupby('Responsável')['Desvio Percentual'].mean().reset_index()
    desvio_por_dev = desvio_por_dev.sort_values('Desvio Percentual')
    
    # Definir cores baseadas no desvio
    colors = ['#e74c3c' if x < 0 else '#27ae60' for x in desvio_por_dev['Desvio Percentual']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=desvio_por_dev['Responsável'],
            y=desvio_por_dev['Desvio Percentual'],
            marker_color=colors,
            text=[f"{x:+.1f}%" for x in desvio_por_dev['Desvio Percentual']],
            textposition='outside',
            textfont=dict(size=11, weight='bold'),
            hovertemplate='<b>%{x}</b><br>Desvio médio: %{y:+.1f}%<extra></extra>',
            name='Desvio Percentual'
        )
    ])
    
    # Adicionar linha de referência no zero
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="#34495e",
        line_width=2,
        annotation_text="🎯 Meta: 0% de desvio",
        annotation_position="top right",
        annotation_font=dict(size=12, color="#34495e")
    )
    
    fig.update_layout(
        title={
            'text': '📈 Precisão das Estimativas por Desenvolvedor',
            'x': 0.5,
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title='Desenvolvedores',
        yaxis_title='Desvio Percentual (%)',
        height=500,
        margin=dict(t=100, b=80, l=60, r=60),
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis={
            'tickfont': {'size': 11}
        },
        yaxis={
            'tickfont': {'size': 11},
            'zeroline': True,
            'zerolinecolor': '#bdc3c7',
            'zerolinewidth': 1
        }
    )
    
    # Adicionar grid sutil
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_xaxes(showgrid=False)
    
    return fig

def grafico_distribuicao_tarefas(df_tarefas):
    """
    Gráfico de distribuição de tarefas por tipo e status
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Tipo de Tarefa' in df_tarefas.columns:
            tipo_count = df_tarefas['Tipo de Tarefa'].value_counts()
            fig1 = px.pie(
                values=tipo_count.values,
                names=tipo_count.index,
                title='Distribuição por Tipo de Tarefa'
            )
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        if 'Status' in df_tarefas.columns:
            status_count = df_tarefas['Status'].value_counts()
            fig2 = px.pie(
                values=status_count.values,
                names=status_count.index,
                title='Distribuição por Status'
            )
            st.plotly_chart(fig2, use_container_width=True)

def grafico_timeline_tarefas(df_tarefas):
    """
    Timeline das tarefas
    """
    if 'Inicio da tarefa' not in df_tarefas.columns or 'Finalização da tarefa' not in df_tarefas.columns:
        return None
    
    df_timeline = df_tarefas.dropna(subset=['Inicio da tarefa', 'Finalização da tarefa']).copy()
    
    if df_timeline.empty:
        return None
    
    fig = px.timeline(
        df_timeline,
        x_start='Inicio da tarefa',
        x_end='Finalização da tarefa',
        y='Responsável',
        color='Sprint',
        hover_data=['Tarefa', 'Horas trabalhadas'],
        title='📅 Timeline de Tarefas por Desenvolvedor',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        title={
            'text': '📅 Timeline de Tarefas por Desenvolvedor',
            'x': 0.5,
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=550,
        margin=dict(t=100, b=60, l=120, r=60),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis={
            'title': 'Período',
            'tickfont': {'size': 11}
        },
        yaxis={
            'title': 'Desenvolvedores',
            'tickfont': {'size': 11}
        },
        legend={
            'title': 'Sprint',
            'font': {'size': 11}
        }
    )
    
    # Adicionar grid sutil
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    return fig

def metricas_resumo_sustentacao(dados):
    """
    Exibe métricas resumidas de sustentação com contexto sobre story points
    """
    st.subheader("📊 Métricas Executivas - Time de Sustentação")
    
    # Explicação sobre Story Points
    with st.expander("ℹ️ O que são Story Points?", expanded=False):
        st.markdown("""
        **Story Points** são uma unidade de medida ágil que representa:
        - **Complexidade** da tarefa
        - **Esforço** necessário para completar
        - **Incerteza** e riscos envolvidos
        
        **Não representam tempo diretamente**, mas sim a dificuldade relativa entre tarefas.
        
        **Exemplo prático:**
        - Tarefa simples = 1-2 story points
        - Tarefa média = 3-5 story points  
        - Tarefa complexa = 8-13 story points
        """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas de velocidade
    if 'velocidade' in dados:
        df_vel = dados['velocidade']
        velocidade_media_planejada = df_vel['Velocidade Planejada'].mean()
        velocidade_media_real = df_vel['Velocidade Real'].mean()
        desvio_medio = df_vel['Diff'].mean()
        
        with col1:
            st.metric(
                "📋 Capacidade Planejada",
                f"{velocidade_media_planejada:.1f} SP",
                help="Média de Story Points planejados por sprint"
            )
        
        with col2:
            delta_color = "normal"
            st.metric(
                "✅ Capacidade Real",
                f"{velocidade_media_real:.1f} SP",
                f"{velocidade_media_real - velocidade_media_planejada:+.1f} SP",
                delta_color=delta_color,
                help="Média de Story Points efetivamente entregues"
            )
    
    # Calcular taxa de entrega se houver dados de velocidade
    taxa_entrega = 0
    if 'velocidade' in dados:
        df_vel = dados['velocidade']
        velocidade_media_planejada = df_vel['Velocidade Planejada'].mean()
        velocidade_media_real = df_vel['Velocidade Real'].mean()
        taxa_entrega = (velocidade_media_real / velocidade_media_planejada * 100) if velocidade_media_planejada > 0 else 0
    
    # Métricas de tarefas
    if 'tarefas' in dados:
        df_tarefas = dados['tarefas']
        total_tarefas = len(df_tarefas)
        total_devs = df_tarefas['Responsável'].nunique() if 'Responsável' in df_tarefas.columns else 0
        
        with col3:
            taxa_color = "normal"
            st.metric(
                "🎯 Taxa de Entrega",
                f"{taxa_entrega:.1f}%",
                f"{taxa_entrega - 100:+.1f}%",
                delta_color=taxa_color,
                help="Percentual de story points entregues vs planejados"
            )
        
        with col4:
            st.metric(
                "👥 Desenvolvedores",
                total_devs,
                help="Número de desenvolvedores ativos no período"
            )
    
    # Análise adicional de story points
    if 'velocidade' in dados:
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        
        df_vel = dados['velocidade']
        
        with col_a:
            variabilidade = df_vel['Velocidade Real'].std()
            st.metric(
                "📊 Variabilidade",
                f"{variabilidade:.1f} SP",
                help="Desvio padrão da velocidade real (menor = mais previsível)"
            )
        
        with col_b:
            melhor_sprint = df_vel.loc[df_vel['Velocidade Real'].idxmax(), 'Sprint']
            melhor_valor = df_vel['Velocidade Real'].max()
            st.metric(
                "🏆 Melhor Sprint",
                f"{melhor_sprint}",
                f"{melhor_valor:.0f} SP",
                help="Sprint com maior entrega de story points"
            )
        
        with col_c:
            consistencia = len(df_vel[abs(df_vel['Diff']) <= 2]) / len(df_vel) * 100
            st.metric(
                "🎯 Consistência",
                f"{consistencia:.0f}%",
                help="% de sprints com desvio ≤ 2 story points"
             )
    
    # Métricas de horas
    if 'tarefas' in dados and 'Horas trabalhadas' in dados['tarefas'].columns:
        df_tarefas = dados['tarefas']
        total_horas = df_tarefas['Horas trabalhadas'].sum()
        media_horas_tarefa = df_tarefas['Horas trabalhadas'].mean()
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                "Total de Horas",
                f"{total_horas:.1f}h",
                help="Total de horas trabalhadas"
            )
        
        with col6:
            st.metric(
                "Média por Tarefa",
                f"{media_horas_tarefa:.1f}h",
                help="Média de horas por tarefa"
            )
        
        if 'Desvio Percentual' in df_tarefas.columns:
            desvio_medio_perc = df_tarefas['Desvio Percentual'].mean()
            with col7:
                st.metric(
                    "Desvio Médio",
                    f"{desvio_medio_perc:+.1f}%",
                    help="Desvio médio entre horas estimadas e trabalhadas"
                )

def main_sustentacao():
    """
    Função principal do módulo de sustentação
    """
    st.title("🔧 Dashboard de Sustentação")
    st.markdown("---")
    
    # Carregar dados
    dados = carregar_dados_sustentacao()
    
    if not dados:
        st.info("📁 Faça upload das planilhas para começar a análise")
        st.markdown("""
        ### 📋 Planilhas Esperadas:
        
        1. **Planilha de Velocidade** (ex: "Planilha sem título.xlsx")
           - Colunas: Sprint, Velocidade Planejada, Velocidade Real, Diff
           
        2. **Planilha de Tarefas** (ex: "Planilha horas por dev.xlsx")
           - Colunas: Tarefa, Status, Prioridade, Sprint, Responsável, Tipo de Tarefa, 
             Horas estimadas, Horas trabalhadas, etc.
        """)
        return
    
    # Processar dados
    dados_processados = processar_dados_sustentacao(dados)
    
    # Exibir métricas resumidas
    metricas_resumo_sustentacao(dados_processados)
    
    st.markdown("---")
    
    # Criar abas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Velocidade", 
        "👥 Desenvolvedores", 
        "⏱️ Gestão de Tempo", 
        "📋 Dados Detalhados"
    ])
    
    # Aba Velocidade
    with tab1:
        st.header("📈 Análise de Velocidade")
        
        if 'velocidade' in dados_processados:
            df_vel = dados_processados['velocidade']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_vel = grafico_velocidade_sprint(df_vel)
                st.plotly_chart(fig_vel, use_container_width=True)
            
            with col2:
                fig_desvio = grafico_desvio_velocidade(df_vel)
                st.plotly_chart(fig_desvio, use_container_width=True)
            
            # Tabela de velocidade
            st.subheader("📊 Dados de Velocidade")
            st.dataframe(df_vel, use_container_width=True)
            
        else:
            st.warning("⚠️ Dados de velocidade não disponíveis")
    
    # Aba Desenvolvedores
    with tab2:
        st.header("👥 Análise por Desenvolvedor")
        
        if 'tarefas' in dados_processados:
            df_tarefas = dados_processados['tarefas']
            
            # Gráfico de horas por desenvolvedor
            fig_horas = grafico_horas_por_dev(df_tarefas)
            if fig_horas:
                st.plotly_chart(fig_horas, use_container_width=True)
            
            # Distribuição de tarefas
            st.subheader("📊 Distribuição de Tarefas")
            grafico_distribuicao_tarefas(df_tarefas)
            
            # Estatísticas por desenvolvedor
            if 'Responsável' in df_tarefas.columns:
                st.subheader("📈 Estatísticas por Desenvolvedor")
                
                stats_dev = df_tarefas.groupby('Responsável').agg({
                    'Tarefa': 'count',
                    'Horas trabalhadas': ['sum', 'mean'],
                    'Pontuação': 'sum'
                }).round(2)
                
                stats_dev.columns = ['Total Tarefas', 'Total Horas', 'Média Horas/Tarefa', 'Total Pontos']
                st.dataframe(stats_dev, use_container_width=True)
        
        else:
            st.warning("⚠️ Dados de tarefas não disponíveis")
    
    # Aba Gestão de Tempo
    with tab3:
        st.header("⏱️ Gestão de Tempo")
        
        if 'tarefas' in dados_processados:
            df_tarefas = dados_processados['tarefas']
            
            # Gráfico comparativo de horas
            st.markdown("**📊 Comparação de horas estimadas vs trabalhadas por desenvolvedor**")
            st.markdown("""📋 **Descrição:** Este gráfico compara as horas estimadas inicialmente com as horas efetivamente trabalhadas por cada desenvolvedor.
            
**Cores das barras:**
- 🔵 **Azul (Horas Estimadas):** Tempo planejado inicialmente para as tarefas
- 🟢 **Verde (Horas Trabalhadas):** Tempo real gasto na execução das tarefas

**Interpretação:** Quando a barra laranja é maior que a azul, houve estouro de prazo. Quando é menor, a tarefa foi concluída antes do previsto.""")
            fig_comparativo = grafico_comparativo_horas(df_tarefas)
            if fig_comparativo:
                st.plotly_chart(fig_comparativo, use_container_width=True)
            
            # Gráfico de desvio percentual
            st.markdown("**📈 Precisão das estimativas - desvio percentual por desenvolvedor**")
            st.markdown("""📋 **Descrição:** Mostra o desvio percentual médio entre estimativa e execução para cada desenvolvedor.
            
**Cores das barras:**
- 🔴 **Vermelho:** Desvio negativo (gastou menos tempo que o estimado)
- 🟢 **Verde:** Desvio positivo (gastou mais tempo que o estimado)

**Interpretação:** Valores próximos a 0% indicam estimativas precisas. A linha tracejada representa a meta ideal de 0% de desvio.""")
            fig_desvio_percentual = grafico_desvio_percentual(df_tarefas)
            if fig_desvio_percentual:
                st.plotly_chart(fig_desvio_percentual, use_container_width=True)
            
            # Timeline de tarefas
        
            fig_timeline = grafico_timeline_tarefas(df_tarefas)
            if fig_timeline:
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Análise de desvios
            if 'Desvio Horas' in df_tarefas.columns:
                st.subheader("📊 Análise de Desvios")
                
                df_desvios = df_tarefas.dropna(subset=['Desvio Horas'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Maiores desvios positivos
                    maiores_desvios = df_desvios.nlargest(5, 'Desvio Horas')[['Tarefa', 'Responsável', 'Desvio Horas']]
                    st.write("**⚠️ Maiores Desvios (Horas Extras)**")
                    st.dataframe(maiores_desvios, use_container_width=True)
                
                with col2:
                    # Maiores desvios negativos (economia)
                    menores_desvios = df_desvios.nsmallest(5, 'Desvio Horas')[['Tarefa', 'Responsável', 'Desvio Horas']]
                    st.write("**✅ Maiores Economias de Tempo**")
                    st.dataframe(menores_desvios, use_container_width=True)
        
        else:
            st.warning("⚠️ Dados de tarefas não disponíveis")
    
    # Aba Dados Detalhados
    with tab4:
        st.header("📋 Dados Detalhados")
        
        if 'tarefas' in dados_processados:
            st.subheader("📊 Dados de Tarefas")
            df_tarefas = dados_processados['tarefas']
            st.dataframe(df_tarefas, use_container_width=True)
            
            # Download dos dados
            csv = df_tarefas.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="dados_sustentacao.csv",
                mime="text/csv"
            )
        
        if 'velocidade' in dados_processados:
            st.subheader("📈 Dados de Velocidade")
            df_vel = dados_processados['velocidade']
            st.dataframe(df_vel, use_container_width=True)

if __name__ == "__main__":
    main_sustentacao()