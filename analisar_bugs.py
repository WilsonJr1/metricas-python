import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

def carregar_planilha_bugs(caminho_arquivo):
    """
    Carrega e analisa a planilha de bugs
    """
    try:
        df_bugs = pd.read_excel(caminho_arquivo)
        return df_bugs
    except Exception as e:
        st.error(f"Erro ao carregar planilha de bugs: {e}")
        return None

def processar_dados_bugs(df_bugs):
    """
    Processa e limpa os dados da planilha de bugs
    """
    if df_bugs is None or df_bugs.empty:
        return None
    
    # Converter datas se existirem
    colunas_data = [col for col in df_bugs.columns if 'data' in col.lower() or 'date' in col.lower()]
    for col in colunas_data:
        df_bugs[col] = pd.to_datetime(df_bugs[col], errors='coerce')
    
    # Limpar dados nulos e vazios
    df_bugs = df_bugs.dropna(how='all')
    
    return df_bugs

def analisar_estrutura_bugs(df_bugs):
    """
    Analisa a estrutura da planilha de bugs
    """
    if df_bugs is None:
        return None
    
    analise = {
        'total_registros': len(df_bugs),
        'colunas': list(df_bugs.columns),
        'tipos_dados': df_bugs.dtypes.to_dict(),
        'valores_nulos': df_bugs.isnull().sum().to_dict(),
        'amostra_dados': df_bugs.head().to_dict('records')
    }
    
    return analise

def gerar_metricas_bugs(df_bugs):
    """
    Gera métricas específicas para bugs
    """
    if df_bugs is None or df_bugs.empty:
        return {}
    
    metricas = {
        'total_bugs': len(df_bugs),
        'bugs_por_severidade': {},
        'bugs_por_status': {},
        'bugs_por_categoria': {},
        'bugs_por_periodo': {}
    }
    
    # Análise por severidade (se existir coluna)
    colunas_severidade = [col for col in df_bugs.columns if any(palavra in col.lower() for palavra in ['severidade', 'severity', 'prioridade', 'priority'])]
    if colunas_severidade:
        col_sev = colunas_severidade[0]
        metricas['bugs_por_severidade'] = df_bugs[col_sev].value_counts().to_dict()
    
    # Análise por status (se existir coluna)
    colunas_status = [col for col in df_bugs.columns if 'status' in col.lower()]
    if colunas_status:
        col_status = colunas_status[0]
        metricas['bugs_por_status'] = df_bugs[col_status].value_counts().to_dict()
    
    # Análise por categoria/tipo (se existir coluna)
    colunas_categoria = [col for col in df_bugs.columns if any(palavra in col.lower() for palavra in ['categoria', 'tipo', 'type', 'category'])]
    if colunas_categoria:
        col_cat = colunas_categoria[0]
        metricas['bugs_por_categoria'] = df_bugs[col_cat].value_counts().to_dict()
    
    # Análise temporal (se existir coluna de data)
    colunas_data = [col for col in df_bugs.columns if 'data' in col.lower() or 'date' in col.lower()]
    if colunas_data:
        col_data = colunas_data[0]
        df_bugs_com_data = df_bugs.dropna(subset=[col_data])
        if not df_bugs_com_data.empty:
            df_bugs_com_data['mes_ano'] = df_bugs_com_data[col_data].dt.to_period('M')
            metricas['bugs_por_periodo'] = df_bugs_com_data['mes_ano'].value_counts().sort_index().to_dict()
    
    return metricas

def criar_graficos_bugs(df_bugs, metricas):
    """
    Cria gráficos específicos para análise de bugs
    """
    graficos = {}
    
    if not metricas:
        return graficos
    
    # Gráfico de bugs por severidade
    if metricas['bugs_por_severidade']:
        fig_sev = px.pie(
            values=list(metricas['bugs_por_severidade'].values()),
            names=list(metricas['bugs_por_severidade'].keys()),
            title="🚨 Distribuição de Bugs por Severidade",
            color_discrete_sequence=['#FF6B6B', '#FFA726', '#FFEB3B', '#4CAF50']
        )
        graficos['severidade'] = fig_sev
    
    # Gráfico de bugs por status
    if metricas['bugs_por_status']:
        fig_status = px.bar(
            x=list(metricas['bugs_por_status'].keys()),
            y=list(metricas['bugs_por_status'].values()),
            title="📊 Bugs por Status",
            color=list(metricas['bugs_por_status'].values()),
            color_continuous_scale='Reds'
        )
        graficos['status'] = fig_status
    
    # Gráfico de bugs por categoria
    if metricas['bugs_por_categoria']:
        fig_cat = px.bar(
            y=list(metricas['bugs_por_categoria'].keys()),
            x=list(metricas['bugs_por_categoria'].values()),
            orientation='h',
            title="🔍 Bugs por Categoria/Tipo",
            color=list(metricas['bugs_por_categoria'].values()),
            color_continuous_scale='Blues'
        )
        graficos['categoria'] = fig_cat
    
    # Gráfico temporal
    if metricas['bugs_por_periodo']:
        periodos = [str(p) for p in metricas['bugs_por_periodo'].keys()]
        valores = list(metricas['bugs_por_periodo'].values())
        
        fig_tempo = px.line(
            x=periodos,
            y=valores,
            title="📈 Evolução de Bugs ao Longo do Tempo",
            markers=True
        )
        fig_tempo.update_traces(line_color='#FF6B6B', marker_size=8)
        graficos['temporal'] = fig_tempo
    
    return graficos

def exibir_dashboard_bugs(df_bugs):
    """
    Exibe o dashboard específico para análise de bugs
    """
    if df_bugs is None:
        st.error("❌ Não foi possível carregar os dados de bugs")
        return
    
    st.markdown("### 🐛 **Análise Detalhada de Bugs**")
    st.markdown("*Insights profissionais sobre defeitos identificados*")
    
    # Análise da estrutura
    analise = analisar_estrutura_bugs(df_bugs)
    
    # Métricas
    metricas = gerar_metricas_bugs(df_bugs)
    
    # Gráficos
    graficos = criar_graficos_bugs(df_bugs, metricas)
    
    # Exibir métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🐛 Total de Bugs", metricas.get('total_bugs', 0))
    
    with col2:
        if metricas['bugs_por_severidade']:
            bugs_criticos = sum([v for k, v in metricas['bugs_por_severidade'].items() if 'crítico' in k.lower() or 'critical' in k.lower() or 'alto' in k.lower() or 'high' in k.lower()])
            st.metric("🚨 Bugs Críticos", bugs_criticos)
    
    with col3:
        if metricas['bugs_por_status']:
            bugs_abertos = sum([v for k, v in metricas['bugs_por_status'].items() if 'aberto' in k.lower() or 'open' in k.lower() or 'novo' in k.lower() or 'new' in k.lower()])
            st.metric("🔓 Bugs Abertos", bugs_abertos)
    
    with col4:
        if metricas['bugs_por_status']:
            bugs_resolvidos = sum([v for k, v in metricas['bugs_por_status'].items() if 'resolvido' in k.lower() or 'resolved' in k.lower() or 'fechado' in k.lower() or 'closed' in k.lower()])
            st.metric("✅ Bugs Resolvidos", bugs_resolvidos)
    
    st.markdown("---")
    
    # Exibir gráficos
    if graficos:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            if 'severidade' in graficos:
                st.plotly_chart(graficos['severidade'], use_container_width=True)
            elif 'status' in graficos:
                st.plotly_chart(graficos['status'], use_container_width=True)
        
        with col_graf2:
            if 'categoria' in graficos:
                st.plotly_chart(graficos['categoria'], use_container_width=True)
            elif 'temporal' in graficos:
                st.plotly_chart(graficos['temporal'], use_container_width=True)
        
        # Gráfico temporal em linha separada se existir
        if 'temporal' in graficos and 'categoria' in graficos:
            st.plotly_chart(graficos['temporal'], use_container_width=True)
    
    # Tabela de dados
    if st.checkbox("📊 Mostrar dados detalhados de bugs"):
        st.dataframe(df_bugs, use_container_width=True)
        st.caption(f"Total de registros: {len(df_bugs)}")
    
    # Insights automáticos
    st.markdown("### 💡 **Insights Automáticos**")
    
    insights = []
    
    if metricas['bugs_por_severidade']:
        total_bugs = sum(metricas['bugs_por_severidade'].values())
        bugs_criticos = sum([v for k, v in metricas['bugs_por_severidade'].items() if 'crítico' in k.lower() or 'critical' in k.lower()])
        if bugs_criticos > 0:
            perc_criticos = (bugs_criticos / total_bugs) * 100
            insights.append(f"🚨 **{perc_criticos:.1f}%** dos bugs são críticos - requer atenção imediata")
    
    if metricas['bugs_por_status']:
        bugs_abertos = sum([v for k, v in metricas['bugs_por_status'].items() if 'aberto' in k.lower() or 'open' in k.lower()])
        total_bugs = sum(metricas['bugs_por_status'].values())
        if bugs_abertos > 0:
            perc_abertos = (bugs_abertos / total_bugs) * 100
            insights.append(f"🔓 **{perc_abertos:.1f}%** dos bugs ainda estão abertos")
    
    if metricas['bugs_por_categoria']:
        categoria_mais_comum = max(metricas['bugs_por_categoria'], key=metricas['bugs_por_categoria'].get)
        insights.append(f"🔍 **{categoria_mais_comum}** é a categoria com mais bugs")
    
    for insight in insights:
        st.info(insight)
    
    return analise, metricas, graficos

if __name__ == "__main__":
    # Teste local
    caminho_bugs = "bugs.xlsx"
    df_bugs = carregar_planilha_bugs(caminho_bugs)
    if df_bugs is not None:
        df_bugs = processar_dados_bugs(df_bugs)
        exibir_dashboard_bugs(df_bugs)