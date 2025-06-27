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
    
    colunas_esperadas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
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



def grafico_status_distribuicao(df_filtrado):
    if 'Status' in df_filtrado.columns:
        status_counts = df_filtrado['Status'].value_counts()
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title="🎯 Resultado dos Testes de Qualidade",
            color_discrete_sequence=['#4ECDC4', '#45B7D1', '#6C5CE7', '#96CEB4', '#FECA57']
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
        fig.update_coloraxes(colorbar_title="Quantidade de Tasks")
        fig.update_layout(
            showlegend=False, 
            height=max(450, len(time_counts) * 45),
            margin=dict(t=50, b=80, l=200, r=150)
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
            
            fig = px.bar(
                timeline_data,
                x='Mes',
                y='Count',
                color='Status',
                title="📈 Evolução dos Testes de Qualidade",
                labels={'Count': 'Tasks Testadas por Dia', 'Mes': 'Mês'},
                text='Count'
            )
            fig.update_layout(
                margin=dict(t=50, b=80, l=80, r=80),
                height=450
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
                    margin=dict(t=50, b=80, l=250, r=150),
                    height=max(450, len(motivos_counts) * 40)
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
                fig.update_coloraxes(colorbar_title="Taxa de Rejeição (%)")
                fig.update_layout(
                    margin=dict(t=50, b=120, l=120, r=80),
                    height=450
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
                marker_color='#FF6B6B'
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
    col1, col2, col3 = st.columns(3)
    
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
    
    # Removido: Equipe Q.A Ativa
    
    # === SEÇÃO 2: IMPACTO NA QUALIDADE ===
    st.markdown("##### 🛡️ **Impacto na Qualidade e Prevenção de Defeitos**")
    col5, col6, col7 = st.columns(3)
    
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
    
    # Removido: Valor Economizado
    
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
    
    # === RESUMO EXECUTIVO REMOVIDO ===
    # Seção removida conforme solicitação


def main():
    st.set_page_config(
        page_title="Dashboard de Tasks",
        page_icon="📊",
        layout="wide"
    )
    
    # Título principal
    st.title("📊 Painel de Métricas de Qualidade")
    
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📌 Visão Geral Estratégica", "🛡️ Prevenção e Qualidade", "🏁 Visão por Sprint", "🧑‍🤝‍🧑 Visão por Testador", "📋 Tarefas Sem Teste"])
        
        with tab1:
            st.markdown("### 📌 **Visão Geral Estratégica**")
            st.markdown("*Cobertura e impacto do time de Q.A*")
            
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
            st.markdown("### 🛡️ **Prevenção e Qualidade**")
            st.markdown("*Bugs identificados, tipos de falha e taxas de aprovação*")
            
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
            st.markdown("#### 🔍 **Tipos de Falha e Motivos**")
            
            col_motivos1, col_motivos2 = st.columns(2)
            
            with col_motivos1:
                # Tipo de falha mais comum
                fig_motivos = grafico_motivos_rejeicao(df_com_teste)
                if fig_motivos:
                    # Melhorar cores e destacar o mais comum
                    fig_motivos.update_traces(
                        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'],
                        text=[f'✅ Mais comum' if i == 0 else '' for i in range(len(fig_motivos.data[0].x))],
                        textposition='outside'
                    )
                    fig_motivos.update_layout(title_font_color='#FFFFFF')
                    st.plotly_chart(fig_motivos, use_container_width=True, key="motivos_rejeicao_principal")
            
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
                            color_discrete_sequence=['#4ECDC4', '#FF6B6B'],
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
            st.markdown("#### 👨‍💻 **Análise por Desenvolvedor**")
            
            # Novo gráfico: Motivos de recusa por desenvolvedor
            fig_motivos_dev = grafico_motivos_recusa_por_dev(df_com_teste)
            if fig_motivos_dev:
                st.plotly_chart(fig_motivos_dev, use_container_width=True, key="motivos_recusa_por_dev")
            else:
                st.info("📋 Dados insuficientes para análise de motivos por desenvolvedor (mínimo 2 rejeições por dev)")
            
            st.markdown("---")
            st.markdown("#### 📈 **Evolução de Taxa ao Longo do Tempo**")
            
            # Melhorar gráfico de evolução
            fig_evolucao = grafico_evolucao_qualidade(df_com_teste)
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
        
        with tab4:
            st.markdown("### 🧑‍🤝‍🧑 **Visão por Testador**")
            st.markdown("*Ranking de performance, produtividade e comparação entre testadores*")
            
            if 'Responsavel pelo teste' in df_com_teste.columns and not df_com_teste.empty:
                testador_stats = df_com_teste.groupby('Responsavel pelo teste').agg({
                    'Status': ['count', lambda x: (x == 'REJEITADA').sum(), lambda x: (x == 'APROVADA').sum()]
                }).round(1)
                
                testador_stats.columns = ['Total_Testes', 'Bugs_Encontrados', 'Testes_Aprovados']
                testador_stats['Taxa_Deteccao'] = (testador_stats['Bugs_Encontrados'] / testador_stats['Total_Testes'] * 100).round(1)
                testador_stats['Taxa_Aprovacao'] = (testador_stats['Testes_Aprovados'] / testador_stats['Total_Testes'] * 100).round(1)
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
                    fig_prod.update_coloraxes(colorbar_title="Total de Testes")
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
                        color_discrete_sequence=['#4ECDC4', '#FF6B6B'],
                        barmode='group'
                    )
                    fig_taxas.update_layout(
                        title_font_color='#FFFFFF',
                        xaxis_title='Testador',
                        yaxis_title='Percentual (%)',
                        legend_title='Métricas',
                        margin=dict(t=50, b=120, l=80, r=80),
                        height=450
                    )
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
                
                st.plotly_chart(fig_comp, use_container_width=True, key="comparativo_produtividade_detalhado")
                
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
                
                st.plotly_chart(fig_taxa, use_container_width=True, key="comparativo_taxas_detalhado")
            

        
        with tab4:
            st.markdown("### 📋 **Dados Detalhados**")
            st.markdown("*Visualização completa dos dados de testes realizados pelo time de Q.A*")
            
            if st.checkbox("Mostrar dados dos testes efetuados", key="show_data_checkbox"):
                st.dataframe(df_com_teste, use_container_width=True)
                st.caption(f"Total de testes efetuados exibidos: {len(df_com_teste)}")
        
        with tab5:
            st.markdown("### 📋 **Tarefas Sem Teste**")
            st.markdown("*Análise detalhada das tarefas que não passaram por testes de qualidade*")
            
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
        
        ### 🚀 Funcionalidades do Dashboard:
        - Análise de performance por sprint
        - Métricas de qualidade e rejeições
        - Visualizações interativas
        - Filtros avançados por período e responsável
        - Exportação de dados
        """)

if __name__ == "__main__":
    main()