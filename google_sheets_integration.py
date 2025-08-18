import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
from datetime import datetime, timedelta

def get_service_account_info():
    """
    Obtém as credenciais da service account dos secrets do Streamlit
    """
    try:
        return {
            "type": "service_account",
            "project_id": st.secrets["google_sheets"]["project_id"],
            "private_key_id": st.secrets["google_sheets"]["private_key_id"],
            "private_key": st.secrets["google_sheets"]["private_key"],
            "client_email": st.secrets["google_sheets"]["client_email"],
            "client_id": st.secrets["google_sheets"]["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets["google_sheets"]["client_x509_cert_url"],
            "universe_domain": "googleapis.com"
        }
    except KeyError as e:
        st.error(f"Configuração de secrets incompleta: {e}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar secrets: {e}")
        return None

def get_spreadsheet_config():
    """
    Obtém a configuração da planilha dos secrets do Streamlit
    """
    try:
        return {
            "url": st.secrets["google_sheets"]["spreadsheet_url"],
            "worksheet_name": st.secrets["google_sheets"]["worksheet_name"]
        }
    except KeyError as e:
        st.error(f"Configuração da planilha incompleta: {e}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar configuração da planilha: {e}")
        return None

import time

class GoogleSheetsConnector:
    def __init__(self):
        self.gc = None
        self.worksheet = None
        self.last_update = None
        self.cache_duration = 300  # 5 minutos em segundos
        self.cached_data = None
        
    def setup_credentials_from_json(self, credentials_json):
        """
        Configura as credenciais a partir de um JSON de service account
        """
        try:
            # Escopo necessário para Google Sheets
            scope = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Criar credenciais a partir do JSON
            credentials_dict = json.loads(credentials_json)
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
            
            # Autorizar o cliente gspread
            self.gc = gspread.authorize(credentials)
            return True, "Credenciais configuradas com sucesso!"
            
        except json.JSONDecodeError:
            return False, "Erro: JSON de credenciais inválido"
        except Exception as e:
            return False, f"Erro ao configurar credenciais: {str(e)}"
    
    def connect_to_sheet(self, sheet_url):
        """
        Conecta a uma planilha do Google Sheets usando a URL
        """
        try:
            if not self.gc:
                return False, "Credenciais não configuradas"
            
            # Extrair o ID da planilha da URL
            if '/spreadsheets/d/' in sheet_url:
                sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
            else:
                return False, "URL da planilha inválida"
            
            # Abrir a planilha
            spreadsheet = self.gc.open_by_key(sheet_id)
            
            # Pegar a primeira aba ou a aba especificada na URL
            if '#gid=' in sheet_url:
                gid = sheet_url.split('#gid=')[1]
                try:
                    self.worksheet = spreadsheet.get_worksheet_by_id(int(gid))
                except:
                    self.worksheet = spreadsheet.sheet1
            else:
                self.worksheet = spreadsheet.sheet1
            
            return True, f"Conectado à planilha: {spreadsheet.title}"
            
        except gspread.SpreadsheetNotFound:
            return False, "Planilha não encontrada. Verifique se o service account tem acesso."
        except Exception as e:
            return False, f"Erro ao conectar à planilha: {str(e)}"
    
    def get_data(self, force_refresh=False):
        """
        Obtém os dados da planilha com cache
        """
        try:
            if not self.worksheet:
                return None, "Não conectado a nenhuma planilha"
            
            # Verificar se deve usar cache
            now = datetime.now()
            if (not force_refresh and 
                self.cached_data is not None and 
                self.last_update and 
                (now - self.last_update).seconds < self.cache_duration):
                return self.cached_data, "Dados obtidos do cache"
            
            # Obter todos os dados da planilha
            data = self.worksheet.get_all_records()
            
            if not data:
                return None, "Planilha vazia ou sem dados"
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            # Processar colunas de data se existirem
            date_columns = ['Data', 'data', 'DATE', 'Date']
            for col in date_columns:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass
            
            # Atualizar cache
            self.cached_data = df
            self.last_update = now
            
            return df, f"Dados atualizados com sucesso! {len(df)} registros obtidos."
            
        except Exception as e:
            return None, f"Erro ao obter dados: {str(e)}"
    
    def get_sheet_info(self):
        """
        Obtém informações sobre a planilha conectada
        """
        if not self.worksheet:
            return None
        
        try:
            return {
                'title': self.worksheet.spreadsheet.title,
                'worksheet_title': self.worksheet.title,
                'rows': self.worksheet.row_count,
                'cols': self.worksheet.col_count,
                'last_update': self.last_update.strftime('%d/%m/%Y %H:%M:%S') if self.last_update else 'Nunca'
            }
        except:
            return None

def create_google_sheets_interface():
    """
    Cria a interface do Streamlit para configuração do Google Sheets
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Integração Google Sheets")
    
    # Inicializar o conector na sessão
    if 'sheets_connector' not in st.session_state:
        st.session_state.sheets_connector = GoogleSheetsConnector()
    
    connector = st.session_state.sheets_connector
    
    # Configuração de credenciais
    with st.sidebar.expander("⚙️ Configurar Credenciais", expanded=False):
        st.markdown("""
        **Como configurar:**
        1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
        2. Crie um projeto ou selecione um existente
        3. Ative a API do Google Sheets
        4. Crie uma Service Account
        5. Baixe o arquivo JSON das credenciais
        6. Cole o conteúdo do JSON abaixo
        """)
        
        credentials_json = st.text_area(
            "JSON das Credenciais:",
            height=100,
            placeholder='{"type": "service_account", "project_id": "...", ...}',
            help="Cole aqui o conteúdo completo do arquivo JSON da service account"
        )
        
        if st.button("🔑 Configurar Credenciais"):
            if credentials_json.strip():
                success, message = connector.setup_credentials_from_json(credentials_json)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Por favor, insira o JSON das credenciais")
    
    # Configuração da planilha
    sheet_url = st.sidebar.text_input(
        "🔗 URL da Planilha:",
        value="https://docs.google.com/spreadsheets/d/146PCK64ufCpyQ5VM3l8dZ6RFwOo6c7Ew_1D2zKqvVA4/edit?gid=94752619#gid=94752619",
        help="Cole aqui a URL completa da planilha do Google Sheets"
    )
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔗 Conectar"):
            if sheet_url.strip():
                success, message = connector.connect_to_sheet(sheet_url)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Por favor, insira a URL da planilha")
    
    with col2:
        if st.button("🔄 Atualizar"):
            if connector.worksheet:
                data, message = connector.get_data(force_refresh=True)
                if data is not None:
                    st.success(message)
                    st.session_state.google_sheets_data = data
                else:
                    st.error(message)
            else:
                st.warning("Conecte-se a uma planilha primeiro")
    
    # Mostrar informações da planilha conectada
    sheet_info = connector.get_sheet_info()
    if sheet_info:
        st.sidebar.success("✅ Conectado!")
        with st.sidebar.expander("📊 Informações da Planilha"):
            st.write(f"**Planilha:** {sheet_info['title']}")
            st.write(f"**Aba:** {sheet_info['worksheet_title']}")
            st.write(f"**Linhas:** {sheet_info['rows']}")
            st.write(f"**Colunas:** {sheet_info['cols']}")
            st.write(f"**Última atualização:** {sheet_info['last_update']}")
    
    # Configurações de cache
    with st.sidebar.expander("⚡ Configurações de Cache"):
        cache_minutes = st.slider(
            "Duração do cache (minutos):",
            min_value=1,
            max_value=60,
            value=5,
            help="Tempo que os dados ficam em cache antes de uma nova consulta"
        )
        connector.cache_duration = cache_minutes * 60
        
        if st.button("🗑️ Limpar Cache"):
            connector.cached_data = None
            connector.last_update = None
            st.success("Cache limpo!")
    
    return connector

def load_google_sheets_data_automatically():
    """Carrega dados automaticamente da planilha configurada usando secrets"""
    try:
        # Obter configurações dos secrets
        service_account_info = get_service_account_info()
        spreadsheet_config = get_spreadsheet_config()
        
        if not service_account_info or not spreadsheet_config:
            return None
        
        # Verificar se já temos dados em cache
        cache_key = f"auto_sheets_data_{spreadsheet_config['url']}_{spreadsheet_config['worksheet_name']}"
        
        if cache_key in st.session_state:
            cached_data, cached_time = st.session_state[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=5):
                return cached_data
        
        # Configurar credenciais
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(credentials)
        
        # Conectar à planilha
        spreadsheet = client.open_by_url(spreadsheet_config['url'])
        worksheet = spreadsheet.worksheet(spreadsheet_config['worksheet_name'])
        
        # Obter dados
        data = worksheet.get_all_records()
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        # Cache dos dados
        st.session_state[cache_key] = (df, datetime.now())
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {str(e)}")
        return None