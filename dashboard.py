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
        fig.update_layout(showlegend=False)
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
        fig.update_layout(showlegend=False, height=400)
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
                motivos_counts = pd.Series(todos_motivos).value_counts().head(10)
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
                    title="Devs com Mais Rejeições (min. 3 tasks)",
                    labels={'Responsável': 'Desenvolvedor', 'Total_Rejeicoes': 'Total de Rejeições'},
                    color='Percentual_Rejeicao',
                    color_continuous_scale='reds',
                    text='Total_Rejeicoes',
                    hover_data={'Percentual_Rejeicao': ':.1f'}
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
                    title="Evolução da Taxa de Aprovação ao Longo do Tempo",
                    labels={'Taxa_Aprovacao': 'Taxa de Aprovação (%)', 'Mes': 'Mês'},
                    markers=True
                )
                fig.update_traces(hovertemplate='Mês: %{x}<br>Taxa: %{y}%<extra></extra>')
                return fig
    return None



def metricas_resumo(df_original, df_com_teste, df_sem_teste):
    col1, col2, col3, col4 = st.columns(4)
    
    total_planilha = len(df_original)
    total_testes_efetuados = len(df_com_teste)
    total_sem_teste = len(df_sem_teste)
    
    with col1:
        st.metric("📊 Total na Planilha", total_planilha, help="Total de registros na planilha (inclui todos os tipos)")
    
    with col2:
        st.metric("🧪 Testes Efetuados", total_testes_efetuados, help="Total de testes realmente executados pelo time de Q.A")
    
    with col3:
        st.metric("❌ Sem Teste", total_sem_teste, help="Registros marcados como 'SEM TESTE'")
    
    with col4:
        if 'Nome da Task' in df_com_teste.columns:
            tarefas_unicas = df_com_teste['Nome da Task'].nunique()
            st.metric("📋 Tarefas Únicas Testadas", tarefas_unicas, help="Número de tarefas diferentes que foram testadas")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if 'Status' in df_com_teste.columns:
            aprovadas = len(df_com_teste[df_com_teste['Status'] == 'APROVADA'])
            st.metric("✅ Testes Aprovados", aprovadas, help="Testes que passaram na validação de qualidade")
    
    with col6:
        if 'Status' in df_com_teste.columns:
            rejeitadas = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA'])
            st.metric("🚫 Bugs Identificados", rejeitadas, help="Total de problemas detectados antes da produção")
    
    with col7:
        if 'Status' in df_com_teste.columns and total_testes_efetuados > 0:
            rejeitadas = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA'])
            taxa_deteccao = (rejeitadas / total_testes_efetuados * 100)
            st.metric("🔍 Taxa de Detecção de Bugs", f"{taxa_deteccao:.1f}%", help="Percentual de testes com problemas identificados pelo Q.A")
    
    with col8:
        if 'Responsavel pelo teste' in df_com_teste.columns:
            total_testadores = df_com_teste['Responsavel pelo teste'].nunique()
            st.metric("👥 Testadores Ativos", total_testadores, help="Número de profissionais de Q.A envolvidos")


def main():
    st.set_page_config(
        page_title="Dashboard de Tasks",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔍 Dashboard Q.A DelTech - Métricas de Qualidade")
    st.markdown("### Análise do Impacto e Performance do Time de Quality Assurance")
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
        
        st.subheader("📈 Métricas Gerais")
        metricas_resumo(df_original, df_com_teste, df_sem_teste)
        
        if filtros_ativos and not df_com_teste.empty:
            st.info(f"Mostrando {len(df_com_teste)} testes efetuados de {len(df_original)} registros totais.")
        
        st.markdown("---")
        
        st.subheader("📊 Visão Geral dos Testes de Qualidade")
        st.markdown("*Análise abrangente do trabalho realizado pelo time de Q.A*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = grafico_tasks_por_sprint(df_com_teste)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
            
            fig3 = grafico_tasks_por_time(df_com_teste)
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            fig2 = grafico_status_distribuicao(df_com_teste)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            
            fig5 = grafico_timeline_tasks(df_com_teste)
            if fig5:
                st.plotly_chart(fig5, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Análise de Qualidade")
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_motivos = grafico_motivos_rejeicao(df_filtrado)
            if fig_motivos:
                st.plotly_chart(fig_motivos, use_container_width=True)
        
        with col4:
            fig_taxa_dev = grafico_rejeicoes_por_dev(df_filtrado)
            if fig_taxa_dev:
                st.plotly_chart(fig_taxa_dev, use_container_width=True)
            
            fig_evolucao = grafico_evolucao_qualidade(df_filtrado)
            if fig_evolucao:
                st.plotly_chart(fig_evolucao, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📈 Performance dos Testadores Q.A")
        st.markdown("*Análise detalhada da produtividade e eficácia de cada testador*")
        
        fig4 = grafico_responsavel_performance(df_com_teste)
        if fig4:
            st.plotly_chart(fig4, use_container_width=True)
        

        
        st.markdown("---")
        st.subheader("📋 Dados Detalhados dos Testes")
        st.markdown("*Visualização completa dos dados de testes realizados pelo time de Q.A*")
        if st.checkbox("Mostrar dados dos testes efetuados", key="show_data_checkbox"):
            st.dataframe(df_com_teste, use_container_width=True)
            st.caption(f"Total de testes efetuados exibidos: {len(df_com_teste)}")
    
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
        - **Métricas Gerais**: Taxa de aprovação, tasks rejeitadas, período analisado
        - **Filtros Avançados**: Por sprint, status e time
        - **Análise de Qualidade**: Motivos de rejeição e performance dos desenvolvedores
        - **Visualizações**: Gráficos interativos com informações detalhadas
        - **Evolução Temporal**: Acompanhamento da qualidade ao longo do tempo
        """)

if __name__ == "__main__":
    main()