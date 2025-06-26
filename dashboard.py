import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Q.A DelTech",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def carregar_dados():
    uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return None
    return None

def processar_dados(df):
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    
    # Considerar "PRONTO PARA PUBLICAÇÃO" como "APROVADA"
    if 'Status' in df.columns:
        df['Status'] = df['Status'].replace('PRONTO PARA PUBLICAÇÃO', 'APROVADA')
    
    colunas_esperadas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da task', 
                        'Status', 'Responsável', 'Motivo', 'Motivo2', 'Motivo3', 
                        'Responsavel pelo teste', 'ID']
    
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
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
    
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

def contar_total_bugs(df_rejeitadas):
    """Conta o total de bugs considerando Motivo, Motivo2 e Motivo3"""
    if df_rejeitadas.empty:
        return 0
    
    total_bugs = 0
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
    
    for _, row in df_rejeitadas.iterrows():
        # Conta cada motivo não nulo como um bug separado, excluindo não-bugs
        for col in motivos_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                motivo = str(row[col]).strip().lower()
                if motivo not in ['aprovada', 'sem recusa']:
                    total_bugs += 1
    
    return total_bugs

def grafico_tasks_por_sprint(df_filtrado):
    if 'Sprint' in df_filtrado.columns:
        sprint_counts = df_filtrado['Sprint'].value_counts()
        # Ordenar sprints numericamente (Sprint 1, Sprint 2, etc.)
        sprint_order = sorted(sprint_counts.index, key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else float('inf'))
        sprint_counts = sprint_counts.reindex(sprint_order)
        
        fig = px.bar(
            x=sprint_counts.index, 
            y=sprint_counts.values,
            title="📊 Tasks Testadas por Sprint pelo Q.A",
            labels={'x': 'Sprint', 'y': 'Tasks Testadas'},
            color=sprint_counts.values,
            color_continuous_scale='viridis',
            text=sprint_counts.values
        )
        fig.update_layout(
            showlegend=False,
            margin=dict(t=50, b=50, l=100, r=50),
            height=400
        )
        fig.update_traces(textposition='outside', hovertemplate='Sprint: %{x}<br>Tasks Testadas: %{y}<extra></extra>')
        return fig
    return None

def grafico_status_distribuicao(df_filtrado):
    if 'Status' in df_filtrado.columns:
        status_counts = df_filtrado['Status'].value_counts()
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title="🎯 Resultado dos Testes de Qualidade",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(
            textinfo='label+percent+value',
            hovertemplate='Status: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
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
        fig.update_layout(
            showlegend=False, 
            height=max(400, len(time_counts) * 40),
            margin=dict(t=50, b=50, l=150, r=100)
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
                height=max(400, len(perf_data) * 30)
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
            
            fig = px.bar(
                timeline_data,
                x='Mes',
                y='Count',
                color='Status',
                title="📈 Evolução dos Testes de Qualidade",
                labels={'Count': 'Tasks Testadas por Dia', 'Mes': 'Mês'},
                text='Count'
            )
            fig.update_xaxes(tickangle=45)
            fig.update_traces(textposition='outside', hovertemplate='Mês: %{x}<br>Status: %{legendgroup}<br>Tasks Testadas: %{y}<extra></extra>')
            return fig
    return None

def grafico_motivos_rejeicao(df_filtrado):
    if 'Status' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
                    motivos_counts = pd.Series(motivos_filtrados).value_counts().head(10)
                else:
                    return None
                fig = px.bar(
                    x=motivos_counts.values,
                    y=motivos_counts.index,
                    orientation='h',
                    title="🔍 Principais Problemas Detectados pelo Q.A",
                    labels={'x': 'Bugs Identificados', 'y': 'Tipo de Problema'},
                    color=motivos_counts.values,
                    color_continuous_scale='reds',
                    text=motivos_counts.values
                )
                fig.update_layout(
                    margin=dict(t=50, b=50, l=200, r=100),
                    height=max(400, len(motivos_counts) * 35)
                )
                fig.update_traces(textposition='outside', hovertemplate='Problema: %{y}<br>Ocorrências: %{x}<extra></extra>')
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
                    color_continuous_scale='reds',
                    text='Total_Rejeicoes',
                    hover_data={'Percentual_Rejeicao': ':.1f'}
                )
                fig.update_layout(
                    margin=dict(t=50, b=120, l=150, r=50),
                    height=500
                )
                fig.update_xaxes(tickangle=45)
                fig.update_traces(textposition='outside')
                return fig
    return None

def grafico_evolucao_qualidade(df_filtrado):
    if 'Data' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        df_timeline = df_filtrado.dropna(subset=['Data'])
        if not df_timeline.empty:
            df_timeline['Mes'] = df_timeline['Data'].dt.to_period('M')
            monthly_stats = df_timeline.groupby(['Mes', 'Status']).size().unstack(fill_value=0)
            
            if 'APROVADA' in monthly_stats.columns and 'REJEITADA' in monthly_stats.columns:
                monthly_stats['Total'] = monthly_stats.sum(axis=1)
                monthly_stats['Taxa_Aprovacao'] = (monthly_stats['APROVADA'] / monthly_stats['Total'] * 100).round(1)
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
                color_continuous_scale='reds',
                text=erros_por_time.values
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=50, b=80, l=120, r=50),
                height=400
            )
            fig.update_traces(
                textposition='outside',
                hovertemplate='Time: %{x}<br>Bugs: %{y}<extra></extra>'
            )
            fig.update_xaxes(tickangle=45)
            return fig
    return None

def grafico_distribuicao_bugs_tipo(df_filtrado):
    """Gráfico de distribuição dos tipos de bugs mais comuns"""
    if 'Status' in df_filtrado.columns:
        df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
        motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
                    color_discrete_sequence=px.colors.qualitative.Set2
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
                    labels={'x': 'Semana do Ano', 'y': 'Dia da Semana', 'color': 'Testes Realizados'},
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    margin=dict(t=50, b=50, l=100, r=50),
                    height=400
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
                    color_continuous_scale='reds',
                    text='Taxa_Rejeicao'
                )
                fig.update_layout(
                    margin=dict(t=50, b=80, l=120, r=50),
                    height=400
                )
                fig.update_traces(
                    texttemplate='%{text}%',
                    textposition='outside',
                    hovertemplate='Time: %{x}<br>Taxa: %{y}%<extra></extra>'
                )
                fig.update_xaxes(tickangle=45)
                return fig
    return None

def grafico_comparativo_testadores(df_filtrado):
    """Gráfico comparativo de produtividade entre testadores"""
    if 'Responsavel pelo teste' in df_filtrado.columns and 'Status' in df_filtrado.columns:
        testador_stats = df_filtrado.groupby('Responsavel pelo teste').agg({
            'Status': ['count', lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'APROVADA').sum()]
        }).round(1)
        
        testador_stats.columns = ['Total_Testes', 'Bugs_Encontrados', 'Testes_Aprovados']
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
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Bugs Encontrados',
                x=testador_stats['Responsavel pelo teste'],
                y=testador_stats['Bugs_Encontrados'],
                yaxis='y',
                offsetgroup=2,
                marker_color='red'
            ))
            
            fig.add_trace(go.Scatter(
                name='Taxa de Detecção (%)',
                x=testador_stats['Responsavel pelo teste'],
                y=testador_stats['Taxa_Deteccao'],
                yaxis='y2',
                mode='lines+markers',
                marker_color='orange',
                line=dict(width=3)
            ))
            
            fig.update_layout(
                title="👥 Comparativo de Performance entre Testadores",
                xaxis_title="Testador",
                yaxis=dict(title="Quantidade de Testes", side="left"),
                yaxis2=dict(title="Taxa de Detecção (%)", side="right", overlaying="y"),
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
    st.markdown("*Demonstrando o valor agregado e ROI do investimento em Quality Assurance*")
    
    # Cálculos principais
    total_planilha = len(df_original)
    total_testes_efetuados = len(df_filtrado[df_filtrado['Responsavel pelo teste'].notna()])
    total_sem_teste = len(df_sem_teste) if df_sem_teste is not None else len(df_original[df_original['Motivo'].str.upper().str.contains('SEM TESTE', na=False)])
    
    # Métricas de bugs
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA'] if 'Status' in df_filtrado.columns else pd.DataFrame()
    total_bugs_encontrados = contar_total_bugs(df_rejeitadas) if not df_rejeitadas.empty else 0
    aprovadas = len(df_filtrado[df_filtrado['Status'] == 'APROVADA']) if 'Status' in df_filtrado.columns else 0
    
    # === SEÇÃO 1: MÉTRICAS DE VOLUME E COBERTURA ===
    st.markdown("##### 🎯 **Volume de Trabalho e Cobertura**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cobertura_teste = (total_testes_efetuados / total_planilha * 100) if total_planilha > 0 else 0
        st.metric(
            "📊 Cobertura de Testes", 
            f"{cobertura_teste:.1f}%",
            delta=f"{total_testes_efetuados} de {total_planilha} tarefas",
            help="Percentual de tarefas que receberam validação de qualidade"
        )
    
    with col2:
        if 'Nome da Task' in df_filtrado.columns:
            tarefas_unicas = df_filtrado['Nome da Task'].nunique()
        else:
            tarefas_unicas = 0
        st.metric(
            "📋 Tarefas Validadas", 
            f"{tarefas_unicas:,}",
            delta="tarefas únicas testadas",
            help="Número de tarefas diferentes que passaram por validação de qualidade"
        )
    
    with col3:
        if 'Time' in df_filtrado.columns:
            times_atendidos = df_filtrado['Time'].nunique()
        else:
            times_atendidos = 0
        st.metric(
            "🏢 Times Atendidos", 
            f"{times_atendidos}",
            delta="times de desenvolvimento",
            help="Número de times de desenvolvimento com cobertura de Q.A"
        )
    
    with col4:
        if 'Responsavel pelo teste' in df_filtrado.columns:
            testadores_ativos = df_filtrado['Responsavel pelo teste'].nunique()
        else:
            testadores_ativos = 0
        st.metric(
            "👥 Equipe Q.A Ativa", 
            f"{testadores_ativos}",
            delta="profissionais envolvidos",
            help="Número de profissionais de Q.A ativamente testando"
        )
    
    # === SEÇÃO 2: IMPACTO NA QUALIDADE ===
    st.markdown("##### 🛡️ **Impacto na Qualidade e Prevenção de Defeitos**")
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric(
            "🚫 Bugs Interceptados", 
            f"{total_bugs_encontrados:,}",
            delta="problemas evitados em produção",
            help="Total de defeitos identificados e corrigidos antes da entrega"
        )
    
    with col6:
        taxa_deteccao = (total_bugs_encontrados / total_testes_efetuados * 100) if total_testes_efetuados > 0 else 0
        st.metric(
            "🔍 Taxa de Detecção", 
            f"{taxa_deteccao:.1f}%",
            delta="eficiência na identificação",
            help="Percentual de bugs detectados em relação aos testes realizados"
        )
    
    with col7:
        taxa_aprovacao = (aprovadas / total_testes_efetuados * 100) if total_testes_efetuados > 0 else 0
        st.metric(
            "✅ Taxa de Aprovação", 
            f"{taxa_aprovacao:.1f}%",
            delta=f"{aprovadas} testes aprovados",
            help="Percentual de testes que passaram na primeira validação"
        )
    
    with col8:
        # Estimativa de valor economizado (bugs em produção custam 10x mais para corrigir)
        valor_economizado = total_bugs_encontrados * 10
        st.metric(
            "💰 Valor Economizado", 
            f"{valor_economizado:,}x",
            delta="custo evitado (estimativa)",
            help="Estimativa de economia baseada no custo 10x maior de correção em produção"
        )
    
    # === SEÇÃO 3: ANÁLISE DE RISCOS E PONTOS CRÍTICOS ===
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
                    delta=f"{bugs_time_critico} bugs identificados",
                    delta_color="inverse",
                    help="Time que apresentou maior número de defeitos - requer atenção especial"
                )
    
    with col10:
        if not df_rejeitadas.empty:
            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
                        motivo_mais_comum = pd.Series(motivos_filtrados).value_counts().index[0]
                        ocorrencias_motivo = pd.Series(motivos_filtrados).value_counts().iloc[0]
                        st.metric(
                            "🔍 Principal Tipo de Defeito", 
                            f"{motivo_mais_comum[:15]}...",
                            delta=f"{ocorrencias_motivo} ocorrências",
                            delta_color="inverse",
                            help="Tipo de defeito mais frequente - oportunidade de melhoria no processo"
                        )
    
    with col11:
        taxa_sem_teste = (total_sem_teste / total_planilha * 100) if total_planilha > 0 else 0
        st.metric(
            "⚠️ Tarefas Sem Cobertura", 
            f"{taxa_sem_teste:.1f}%",
            delta=f"{total_sem_teste} tarefas",
            delta_color="inverse" if taxa_sem_teste > 20 else "normal",
            help="Percentual de tarefas que não receberam validação de qualidade"
        )
    
    # === RESUMO EXECUTIVO ===
    st.markdown("##### 📋 **Resumo para Diretoria**")
    
    # Criar métricas de resumo em formato mais executivo
    col_resumo1, col_resumo2 = st.columns(2)
    
    with col_resumo1:
        st.info(f"""
        **🎯 EFETIVIDADE DO TIME Q.A:**
        • **{total_bugs_encontrados:,} defeitos** interceptados antes da produção
        • **{taxa_deteccao:.1f}%** de eficiência na detecção de problemas
        • **{cobertura_teste:.1f}%** de cobertura nas tarefas de desenvolvimento
        • **{times_atendidos} times** de desenvolvimento atendidos
        """)
    
    with col_resumo2:
        st.success(f"""
        **💼 VALOR ENTREGUE:**
        • **{valor_economizado:,}x** em custos evitados (estimativa)
        • **{taxa_aprovacao:.1f}%** de taxa de aprovação na primeira validação
        • **{testadores_ativos} profissionais** dedicados à qualidade
        • **{tarefas_unicas:,} tarefas** validadas com sucesso
        """)


def main():
    st.set_page_config(
        page_title="Dashboard de Tasks",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔍 Dashboard Q.A DelTech - Métricas de Qualidade")
    st.markdown("## 🎯 Dashboard Executivo - Apresentação para Diretoria")
    st.markdown("*Demonstrando o valor agregado pelo time de Q.A na entrega de software de qualidade*")
    st.markdown("---")
    
    df = carregar_dados()
    
    if df is not None:
        df = processar_dados(df)
        
        # Filtros avançados
        st.subheader("🔍 Filtros Avançados")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            sprints_disponiveis = ['Todos'] + sorted(df['Sprint'].dropna().unique().tolist()) if 'Sprint' in df.columns else ['Todos']
            sprint_selecionado = st.selectbox("Filtrar por Sprint:", sprints_disponiveis)
        
        with col2:
            status_disponiveis = ['Todos'] + sorted(df['Status'].dropna().unique().tolist()) if 'Status' in df.columns else ['Todos']
            status_selecionado = st.selectbox("Filtrar por Status:", status_disponiveis)
        
        with col3:
            times_disponiveis = ['Todos'] + sorted(df['Time'].dropna().unique().tolist()) if 'Time' in df.columns else ['Todos']
            time_selecionado = st.selectbox("Filtrar por Time:", times_disponiveis)
        
        with col4:
            devs_disponiveis = ['Todos'] + sorted(df['Responsável'].dropna().unique().tolist()) if 'Responsável' in df.columns else ['Todos']
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
        
        if filtros_ativos and not df_com_teste.empty:
            st.info(f"Mostrando {len(df_com_teste)} testes efetuados de {len(df_original)} registros totais.")
        
        st.markdown("---")
        
        # Criar abas para organizar o dashboard
        tab1, tab2, tab3, tab4 = st.tabs(["📈 KPIs Executivos", "📊 Análise Operacional", "👥 Performance da Equipe", "📋 Dados Detalhados"])
        
        with tab1:
            st.markdown("### 🎯 **Métricas Estratégicas para Diretoria**")
            st.markdown("*Demonstrando o valor e ROI do investimento em Quality Assurance*")
            
            # Métricas executivas principais
            metricas_resumo(df_com_teste, df, df_sem_teste)
            
            st.markdown("---")
            
            # Gráficos executivos específicos
            st.markdown("#### 📊 **Indicadores Visuais Estratégicos**")
            
            col_exec1, col_exec2 = st.columns(2)
            
            with col_exec1:
                # Gráfico de evolução da qualidade
                fig_evolucao = grafico_evolucao_qualidade(df_com_teste)
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
        
        with tab2:
            st.markdown("### 📊 **Análise Operacional Detalhada**")
            st.markdown("*Visão técnica e operacional para gestores de Q.A e desenvolvimento*")
            
            # Visão geral operacional
            st.markdown("#### 📊 **Visão Geral dos Testes**")
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = grafico_tasks_por_sprint(df_com_teste)
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True, key="tasks_por_sprint")
                
                fig3 = grafico_tasks_por_time(df_com_teste)
                if fig3:
                    st.plotly_chart(fig3, use_container_width=True, key="tasks_por_time")
            
            with col2:
                fig2 = grafico_status_distribuicao(df_com_teste)
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True, key="tasks_por_responsavel")
                
                fig5 = grafico_timeline_tasks(df_com_teste)
                if fig5:
                    st.plotly_chart(fig5, use_container_width=True, key="tasks_por_status")
            
            st.markdown("---")
            st.markdown("#### 🔍 **Análise de Qualidade e Bugs**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                fig_motivos = grafico_motivos_rejeicao(df_com_teste)
                if fig_motivos:
                    st.plotly_chart(fig_motivos, use_container_width=True, key="motivos_rejeicao")
                
                fig_erros_time = grafico_erros_por_time(df_com_teste)
                if fig_erros_time:
                    st.plotly_chart(fig_erros_time, use_container_width=True, key="erros_por_time_op")
            
            with col4:
                fig_distribuicao_bugs = grafico_distribuicao_bugs_tipo(df_com_teste)
                if fig_distribuicao_bugs:
                    st.plotly_chart(fig_distribuicao_bugs, use_container_width=True, key="distribuicao_bugs")
                
                fig_taxa_rejeicao_time = grafico_taxa_rejeicao_por_time(df_com_teste)
                if fig_taxa_rejeicao_time:
                    st.plotly_chart(fig_taxa_rejeicao_time, use_container_width=True, key="taxa_rejeicao_time")
            
            st.markdown("---")
            st.markdown("#### 📊 **Análise de Performance e Tendências**")
            
            col5, col6 = st.columns(2)
            
            with col5:
                fig_taxa_dev = grafico_rejeicoes_por_dev(df_com_teste)
                if fig_taxa_dev:
                    st.plotly_chart(fig_taxa_dev, use_container_width=True, key="taxa_desenvolvimento")
                
                fig_evolucao = grafico_evolucao_qualidade(df_com_teste)
                if fig_evolucao:
                    st.plotly_chart(fig_evolucao, use_container_width=True, key="evolucao_tendencias")
            
            with col6:
                fig_heatmap = grafico_heatmap_atividade(df_com_teste)
                if fig_heatmap:
                    st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap_atividade")
        
        with tab3:
            st.markdown("### 👥 **Performance da Equipe Q.A**")
            st.markdown("*Análise detalhada da performance individual e comparativa dos testadores*")
            
            if 'Responsavel pelo teste' in df_com_teste.columns and not df_com_teste.empty:
                testador_stats = df_com_teste.groupby('Responsavel pelo teste').agg({
                    'Status': ['count', lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'APROVADA').sum()]
                }).round(1)
                
                testador_stats.columns = ['Total_Testes', 'Bugs_Encontrados', 'Testes_Aprovados']
                testador_stats['Taxa_Deteccao'] = (testador_stats['Bugs_Encontrados'] / testador_stats['Total_Testes'] * 100).round(1)
                testador_stats['Taxa_Aprovacao'] = (testador_stats['Testes_Aprovados'] / testador_stats['Total_Testes'] * 100).round(1)
                testador_stats['Produtividade'] = testador_stats['Total_Testes']
                testador_stats = testador_stats.reset_index()
            
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
                                st.metric("Taxa de Detecção", f"{row['Taxa_Deteccao']:.1f}%")
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
                    st.markdown("🔍 **Taxa de Detecção de Bugs**")
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
                    marker_color='lightblue',
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
                
                st.plotly_chart(fig_comp, use_container_width=True, key="comparativo_produtividade")
                
                fig_taxa = go.Figure()
                
                fig_taxa.add_trace(go.Scatter(
                    name='Taxa de Detecção',
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
                
                st.plotly_chart(fig_taxa, use_container_width=True, key="comparativo_taxas")
            

        
        with tab4:
            st.markdown("### 📋 **Dados Detalhados**")
            st.markdown("*Visualização completa dos dados de testes realizados pelo time de Q.A*")
            
            if st.checkbox("Mostrar dados dos testes efetuados", key="show_data_checkbox"):
                st.dataframe(df_com_teste, use_container_width=True)
                st.caption(f"Total de testes efetuados exibidos: {len(df_com_teste)}")
            
            if not df_sem_teste.empty:
                st.markdown("---")
                st.markdown("#### 📊 **Tarefas Sem Teste**")
                if st.checkbox("Mostrar tarefas sem teste", key="show_sem_teste_checkbox"):
                    st.dataframe(df_sem_teste, use_container_width=True)
                    st.caption(f"Total de tarefas sem teste: {len(df_sem_teste)}")
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
        - **Responsavel pelo teste**: Testador responsável
        - **ID**: Identificador único da task
        
        ### 📊 Funcionalidades do Dashboard:
        - **KPIs Executivos**: Métricas estratégicas para apresentação à diretoria
        - **Análise Operacional**: Visão técnica detalhada para gestores
        - **Performance da Equipe**: Métricas individuais dos testadores
        - **Dados Detalhados**: Visualização completa dos dados
        - **Filtros Avançados**: Por sprint, status, time e período
        - **Visualizações Interativas**: Gráficos com informações detalhadas
        """)

if __name__ == "__main__":
    main()