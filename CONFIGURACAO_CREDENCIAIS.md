# ⚠️ CONFIGURAÇÃO OBRIGATÓRIA - Credenciais do Google Sheets

## 🔧 Como Configurar as Credenciais

Para que o dashboard funcione automaticamente com sua planilha do Google Sheets, você precisa configurar as credenciais reais no arquivo `google_sheets_integration.py`.

### 1. Criar Service Account no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Google Sheets API**:
   - Vá para "APIs & Services" > "Library"
   - Procure por "Google Sheets API" e ative

4. Crie uma **Service Account**:
   - Vá para "APIs & Services" > "Credentials"
   - Clique em "Create Credentials" > "Service Account"
   - Preencha os dados e clique em "Create"

5. Baixe o arquivo JSON das credenciais:
   - Na lista de Service Accounts, clique na que você criou
   - Vá para a aba "Keys"
   - Clique em "Add Key" > "Create new key" > "JSON"
   - Baixe o arquivo

### 2. Configurar Permissões da Planilha

1. Abra sua planilha: https://docs.google.com/spreadsheets/d/146PCK64ufCpyQ5VM3l8dZ6RFwOo6c7Ew_1D2zKqvVA4/edit
2. Clique em "Compartilhar"
3. Adicione o email da Service Account (encontrado no arquivo JSON baixado)
4. Dê permissão de "Visualizador"

### 3. Atualizar o Código

No arquivo `google_sheets_integration.py`, substitua a variável `SERVICE_ACCOUNT_INFO` pelos dados reais do seu arquivo JSON:

```python
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "SEU_PROJECT_ID_REAL",
    "private_key_id": "SUA_PRIVATE_KEY_ID_REAL",
    "private_key": "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_REAL\n-----END PRIVATE KEY-----\n",
    "client_email": "seu-service-account@seu-projeto.iam.gserviceaccount.com",
    "client_id": "SEU_CLIENT_ID_REAL",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seu-service-account%40seu-projeto.iam.gserviceaccount.com"
}
```

### 4. Verificar Nome da Aba

Certifique-se de que o nome da aba na variável `WORKSHEET_NAME` está correto:

```python
WORKSHEET_NAME = "Planilha1"  # Substitua pelo nome real da aba
```

## ✅ Após a Configuração

Depois de configurar as credenciais:
1. Reinicie o dashboard
2. O carregamento será automático
3. Não será mais necessário fazer upload manual

## 🔒 Segurança

- Nunca compartilhe suas credenciais
- Mantenha o arquivo JSON seguro
- Use apenas permissões mínimas necessárias