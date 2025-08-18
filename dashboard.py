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

def carregar_dados():
    # Tentar carregar automaticamente do Google Sheets
    if GOOGLE_SHEETS_AVAILABLE:
        with st.spinner("🔄 Carregando dados do Google Sheets..."):
            df = load_google_sheets_data_automatically()
            if df is not None:
                st.success(f"✅ Dados carregados automaticamente! {len(df)} registros encontrados.")
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
    
    # Considerar "PRONTO PARA PUBLICAÇÃO" como "APROVADA"
    if 'Status' in df.columns:
        df['Status'] = df['Status'].replace('PRONTO PARA PUBLICAÇÃO', 'APROVADA')
    
    colunas_esperadas = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                        'Status', 'Responsável', 'Motivo', 'Motivo2', 'Motivo3', 
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
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
        'Em correção': '#2196F3', # Azul para em correção
        'Em correcao': '#2196F3', # Azul para em correção
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
        color_discrete_sequence=['#4CAF50', '#FF6B6B', '#FFA726']
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

def grafico_motivos_por_time(df_filtrado):
    if df_filtrado.empty or 'Time' not in df_filtrado.columns:
        return None
    
    df_rejeitadas = df_filtrado[df_filtrado['Status'] == 'REJEITADA']
    if df_rejeitadas.empty:
        return None
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
    
    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
        title_font_color='#FFFFFF',
        xaxis_title='Quantidade de Ocorrências',
        yaxis_title='Tipo de Problema',
        margin=dict(t=60, b=80, l=80, r=80),
        height=500,
        yaxis={'categoryorder': 'total ascending'}
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
    
    # Verificar se a coluna 'Responsavel pelo teste' existe
    if 'Responsavel pelo teste' in df_filtrado.columns:
        total_testes_efetuados = len(df_filtrado[df_filtrado['Responsavel pelo teste'].notna()])
    else:
        # Se não existir, usar uma estimativa baseada em status diferentes de vazio
        total_testes_efetuados = len(df_filtrado[df_filtrado['Status'].notna()]) if 'Status' in df_filtrado.columns else len(df_filtrado)
    
    total_sem_teste = len(df_sem_teste) if df_sem_teste is not None else len(df_original[df_original['Motivo'].str.upper().str.contains('SEM TESTE', na=False)]) if 'Motivo' in df_original.columns else 0
    
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
            "🔍 Taxa de Detecção", 
            f"{taxa_deteccao:.1f}%",
            delta=f"🚨 {rejeitadas:,} testes c/ problemas | ✅ {total_testes_efetuados - rejeitadas:,} aprovados",
            help=f"Percentual de testes que identificaram problemas: {rejeitadas:,} de {total_testes_efetuados:,} testes. Taxa ideal: 15-25% (indica qualidade adequada do código)"
        )
    
    with col7:
        taxa_aprovacao = (aprovadas / total_testes_efetuados * 100) if total_testes_efetuados > 0 else 0
        st.metric(
            "✅ Taxa de Aprovação", 
            f"{taxa_aprovacao:.1f}%",
            delta=f"✅ {aprovadas:,} aprovados | 🚨 {total_testes_efetuados - aprovadas:,} rejeitados",
            help=f"Percentual de aprovação na primeira validação: {aprovadas:,} de {total_testes_efetuados:,} testes. Meta recomendada: >75%"
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
            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
                    delta="📊 Motivo, Motivo2, Motivo3 não encontradas",
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
    # Navegação entre módulos
    st.sidebar.title("Navegação")
    modulo_selecionado = st.sidebar.radio(
        "Selecione o módulo:",
        ["🔍 Qualidade (QA)", "🔧 Sustentação"],
        help="Escolha entre o módulo de análise de QA ou o módulo de sustentação"
    )
    
    if modulo_selecionado == "🔧 Sustentação":
        if main_sustentacao:
            main_sustentacao()
        else:
            st.error("❌ Módulo de sustentação não disponível")
        return
    
    # Módulo de QA (código original)
    # Título principal
    st.title("🔍 Dashboard de Métricas Q.A DelTech")
    
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📌 Visão Geral Estratégica", "🛡️ Prevenção e Qualidade", "🏁 Visão por Sprint", "🧑‍🤝‍🧑 Visão por Testador", "📋 Tarefas Sem Teste", "🔢 Análise de Erros", "🐛 Análise de Bugs", "📊 Relatório P.M."])
        
        with tab1:
            st.markdown("### 📌 **Visão Geral Estratégica**")
            st.markdown("*Dashboard Executivo - Impacto e Performance do Time de Qualidade*")
            
            # === RESUMO EXECUTIVO PARA DIRETORIA ===
            st.markdown("#### 🎯 **Resumo Executivo - Principais Indicadores**")
            
            # Calcular métricas principais para o resumo
            total_planilha = len(df)
            total_testes_efetuados = len(df_com_teste)
            cobertura_teste = (total_testes_efetuados / total_planilha * 100) if total_planilha > 0 else 0
            aprovadas = len(df_com_teste[df_com_teste['Status'] == 'APROVADA']) if 'Status' in df_com_teste.columns else 0
            rejeitadas = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA']) if 'Status' in df_com_teste.columns else 0
            taxa_aprovacao = (aprovadas / total_testes_efetuados * 100) if total_testes_efetuados > 0 else 0
            
            # Resumo em destaque
            col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
            
            with col_resumo1:
                status_cobertura = "🟢 Excelente" if cobertura_teste >= 80 else "🟡 Boa" if cobertura_teste >= 60 else "🔴 Crítica"
                st.info(f"**📊 Cobertura de Testes:** {cobertura_teste:.1f}% ({total_testes_efetuados:,}/{total_planilha:,} tarefas)\n\n**Status:** {status_cobertura}")
            
            with col_resumo2:
                status_qualidade = "🟢 Excelente" if taxa_aprovacao >= 75 else "🟡 Boa" if taxa_aprovacao >= 60 else "🔴 Atenção"
                st.info(f"**✅ Taxa de Aprovação:** {taxa_aprovacao:.1f}% ({aprovadas:,}/{total_testes_efetuados:,} testes)\n\n**Status:** {status_qualidade}")
            
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
            
            st.markdown("---")
            
            # === RECOMENDAÇÕES ESTRATÉGICAS PARA DIRETORIA ===
            st.markdown("#### 🎯 **Recomendações Estratégicas**")
            
            if not df_com_teste.empty:
                # Calcular métricas para recomendações
                total_testes = len(df_com_teste)
                aprovados = len(df_com_teste[df_com_teste['Status'] == 'APROVADA'])
                rejeitados = len(df_com_teste[df_com_teste['Status'] == 'REJEITADA'])
                taxa_aprovacao = (aprovados / total_testes * 100) if total_testes > 0 else 0
                
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
                    total_tasks = len(df) if not df.empty else 0
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
                    
                    # Gráfico de motivos de rejeição
                    fig_motivos = grafico_motivos_rejeicao(df_com_teste)
                    if fig_motivos:
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
                            motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
                - Baseada nas colunas 'Motivo', 'Motivo2', 'Motivo3'
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
                    motivos_cols = ['Motivo', 'Motivo2', 'Motivo3']
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
        
        with tab6:
            st.markdown("### 🔢 **Análise de Erros Encontrados**")
            st.markdown("*Análise detalhada dos erros identificados durante os testes*")
            
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
            
            # Carregar dados de bugs
            df_bugs = carregar_dados_bugs()
            
            if df_bugs is not None and not df_bugs.empty:
                # Filtros para análise de bugs
                st.markdown("#### 🔍 **Filtros de Bugs**")
                
                col_bug_f1, col_bug_f2, col_bug_f3, col_bug_f4, col_bug_f5 = st.columns(5)
                
                with col_bug_f1:
                    times_bugs_disponiveis = ['Todos'] + sorted(df_bugs['Time'].dropna().unique().tolist()) if 'Time' in df_bugs.columns else ['Todos']
                    time_bug_selecionado = st.selectbox("Filtrar por Time:", times_bugs_disponiveis, key="filter_time_bugs")
                
                with col_bug_f2:
                    status_bugs_disponiveis = ['Todos'] + sorted(df_bugs['Status'].dropna().unique().tolist()) if 'Status' in df_bugs.columns else ['Todos']
                    status_bug_selecionado = st.selectbox("Filtrar por Status:", status_bugs_disponiveis, key="filter_status_bugs")
                
                with col_bug_f3:
                    prioridade_bugs_disponiveis = ['Todos'] + sorted(df_bugs['Prioridade'].dropna().unique().tolist()) if 'Prioridade' in df_bugs.columns else ['Todos']
                    prioridade_bug_selecionada = st.selectbox("Filtrar por Prioridade:", prioridade_bugs_disponiveis, key="filter_prioridade_bugs")
                
                with col_bug_f4:
                    fonte_bugs_disponiveis = ['Todos'] + sorted(df_bugs['Encontrado por:'].dropna().unique().tolist()) if 'Encontrado por:' in df_bugs.columns else ['Todos']
                    fonte_bug_selecionada = st.selectbox("Filtrar por Fonte:", fonte_bugs_disponiveis, key="filter_fonte_bugs")
                
                with col_bug_f5:
                    if 'Data' in df_bugs.columns and not df_bugs['Data'].dropna().empty:
                        data_bug_min = df_bugs['Data'].min().date()
                        data_bug_max = df_bugs['Data'].max().date()
                        data_bug_range = st.date_input(
                            "Período:",
                            value=(data_bug_min, data_bug_max),
                            min_value=data_bug_min,
                            max_value=data_bug_max,
                            key="filter_data_bugs"
                        )
                    else:
                        data_bug_range = None
                
                # Aplicar filtros aos dados de bugs
                df_bugs_filtrado = df_bugs.copy()
                
                if time_bug_selecionado != 'Todos':
                    df_bugs_filtrado = df_bugs_filtrado[df_bugs_filtrado['Time'] == time_bug_selecionado]
                
                if status_bug_selecionado != 'Todos':
                    df_bugs_filtrado = df_bugs_filtrado[df_bugs_filtrado['Status'] == status_bug_selecionado]
                
                if prioridade_bug_selecionada != 'Todos':
                    df_bugs_filtrado = df_bugs_filtrado[df_bugs_filtrado['Prioridade'] == prioridade_bug_selecionada]
                
                if fonte_bug_selecionada != 'Todos':
                    df_bugs_filtrado = df_bugs_filtrado[df_bugs_filtrado['Encontrado por:'] == fonte_bug_selecionada]
                
                if data_bug_range and len(data_bug_range) == 2 and 'Data' in df_bugs.columns:
                    df_bugs_filtrado = df_bugs_filtrado[
                        (df_bugs_filtrado['Data'].dt.date >= data_bug_range[0]) & 
                        (df_bugs_filtrado['Data'].dt.date <= data_bug_range[1])
                    ]
                
                # Verificar se há filtros ativos para bugs
                filtros_bugs_ativos = (
                    time_bug_selecionado != 'Todos' or 
                    status_bug_selecionado != 'Todos' or 
                    prioridade_bug_selecionada != 'Todos' or 
                    fonte_bug_selecionada != 'Todos' or 
                    (data_bug_range and len(data_bug_range) == 2)
                )
                
                if filtros_bugs_ativos:
                    st.info(f"Mostrando {len(df_bugs_filtrado)} bugs de {len(df_bugs)} registros totais.")
                
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
            st.header("📊 Relatório Detalhado para P.M.")
            st.markdown("### Análise Detalhada de Bugs e Falhas por Tarefa")
            
            # Filtros específicos para o relatório
            col1, col2, col3 = st.columns(3)
            
            with col1:
                times_disponiveis = ['Todos'] + sorted(df_com_teste['Time'].dropna().unique().tolist())
                time_selecionado = st.selectbox("Filtrar por Time:", times_disponiveis, key="pm_time")
            
            with col2:
                status_disponiveis = ['Todos'] + sorted(df_com_teste['Status'].dropna().unique().tolist())
                status_selecionado = st.selectbox("Filtrar por Status:", status_disponiveis, key="pm_status")
            
            with col3:
                periodo_dias = st.selectbox("Período:", [7, 15, 30, 60, 90, 'Todos'], index=2, key="pm_periodo")
            
            # Aplicar filtros
            df_pm = df_com_teste.copy()
            
            if time_selecionado != 'Todos':
                df_pm = df_pm[df_pm['Time'] == time_selecionado]
            
            if status_selecionado != 'Todos':
                df_pm = df_pm[df_pm['Status'] == status_selecionado]
            
            if periodo_dias != 'Todos':
                data_limite = datetime.now() - pd.Timedelta(days=periodo_dias)
                df_pm = df_pm[df_pm['Data'] >= data_limite]
            
            # Separar dados por tipo de problema
            df_rejeitadas = df_pm[df_pm['Status'] == 'REJEITADA'].copy()
            df_temp = df_pm.copy()
            df_temp['Erros'] = pd.to_numeric(df_temp['Erros'], errors='coerce').fillna(0)
            df_com_erros = df_temp[df_temp['Erros'].notna() & (df_temp['Erros'] > 0)].copy()
            
            # Seção 1: Resumo Executivo
            st.markdown("#### 📈 Resumo Executivo")
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
                total_rejeitadas = len(df_rejeitadas)
                taxa_rejeicao = (total_rejeitadas / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("Tarefas Rejeitadas", total_rejeitadas, f"{taxa_rejeicao:.1f}%")
            
            with col3:
                total_com_erros = len(df_com_erros)
                st.metric("Tarefas com Erros", total_com_erros)
            
            with col4:
                total_problemas = total_rejeitadas + total_com_erros
                st.metric("Total de Problemas", total_problemas)
            
            st.divider()
            
            # Seção 2: Detalhamento de Tarefas Rejeitadas
            if len(df_rejeitadas) > 0:
                st.markdown("#### 🚫 Detalhamento de Tarefas Rejeitadas")
                
                # Criar tabela detalhada com descrição dos problemas
                df_rejeitadas_detalhada = df_rejeitadas[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                       'Responsável', 'Motivo', 'Motivo2', 'Motivo3', 'Responsavel pelo teste']].copy()
                
                # Criar coluna de descrição consolidada
                def criar_descricao_problema(row):
                    motivos = []
                    if pd.notna(row['Motivo']) and row['Motivo'].strip():
                        motivos.append(f"• {row['Motivo'].strip()}")
                    if pd.notna(row['Motivo2']) and row['Motivo2'].strip():
                        motivos.append(f"• {row['Motivo2'].strip()}")
                    if pd.notna(row['Motivo3']) and row['Motivo3'].strip():
                        motivos.append(f"• {row['Motivo3'].strip()}")
                    
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
            
            # Seção 3: Detalhamento de Tarefas com Erros
            if len(df_com_erros) > 0:
                st.markdown("#### ⚠️ Detalhamento de Tarefas com Erros")
                
                df_erros_detalhada = df_com_erros[['Data', 'Sprint', 'Time', 'Nome da Task', 'Link da Task', 
                                                 'Responsável', 'Erros', 'Status', 'Responsavel pelo teste']].copy()
                
                # Criar descrição para erros
                def criar_descricao_erro(row):
                    num_erros = int(row['Erros']) if pd.notna(row['Erros']) else 0
                    status = row['Status'] if pd.notna(row['Status']) else 'N/A'
                    
                    if num_erros == 1:
                        return f"1 erro encontrado (Status: {status})"
                    elif num_erros > 1:
                        return f"{num_erros} erros encontrados (Status: {status})"
                    else:
                        return "Erro não quantificado"
                
                df_erros_detalhada['Descrição do Erro'] = df_erros_detalhada.apply(criar_descricao_erro, axis=1)
                
                colunas_erros = ['Data', 'Sprint', 'Time', 'Nome da Task', 'Responsável', 
                               'Descrição do Erro', 'Responsavel pelo teste', 'Link da Task']
                
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
                        "Descrição do Erro": st.column_config.TextColumn(
                            "Descrição do Erro",
                            help="Detalhes dos erros encontrados"
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
            
            # Seção 4: Análise de Tendências
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
            
            # Seção 5: Recomendações
            st.markdown("#### 💡 Recomendações para P.M.")
            
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
                    for col in ['Motivo', 'Motivo2', 'Motivo3']:
                        motivos_todos.extend(df_rejeitadas[col].dropna().tolist())
                    
                    if motivos_todos:
                        motivo_mais_comum = pd.Series(motivos_todos).value_counts().index[0]
                        recomendacoes.append(f"🎯 **Motivo mais comum**: {motivo_mais_comum}")
                
                for rec in recomendacoes:
                    st.markdown(rec)
            else:
                st.info("Nenhum dado disponível para análise com os filtros selecionados.")
            
            st.markdown("""
            ---
            **💼 Sobre este Relatório:**
            
            Este relatório foi desenvolvido especificamente para fornecer à P.M. uma visão detalhada dos problemas encontrados nas tarefas, 
            incluindo descrições específicas dos bugs e falhas. Os dados podem ser exportados em CSV para análises adicionais ou 
            apresentações executivas.
            
            **📋 Como usar:**
            1. Use os filtros no topo para focar em times, períodos ou status específicos
            2. Analise as tabelas detalhadas para entender os problemas específicos
            3. Exporte os dados em CSV para análises offline
            4. Use as tendências e recomendações para tomada de decisão
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