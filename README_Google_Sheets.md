# Integração com Google Sheets

## Como Configurar

### 1. Criar Credenciais do Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google Sheets:
   - Vá para "APIs & Services" > "Library"
   - Procure por "Google Sheets API" e ative
4. Crie uma Service Account:
   - Vá para "APIs & Services" > "Credentials"
   - Clique em "Create Credentials" > "Service Account"
   - Preencha os dados e clique em "Create"
5. Baixe o arquivo JSON das credenciais:
   - Na lista de Service Accounts, clique na que você criou
   - Vá para a aba "Keys"
   - Clique em "Add Key" > "Create new key" > "JSON"
   - Salve o arquivo como `credentials.json` na pasta do projeto

### 2. Configurar Permissões da Planilha

1. Abra sua planilha no Google Sheets
2. Clique em "Compartilhar"
3. Adicione o email da Service Account (encontrado no arquivo credentials.json)
4. Dê permissão de "Visualizador" ou "Editor"

### 3. Usar no Dashboard

1. Execute o dashboard: `streamlit run dashboard.py`
2. Na aba "🔗 Google Sheets":
   - Faça upload do arquivo `credentials.json`
   - Cole a URL da sua planilha
   - Selecione a aba desejada
   - Clique em "Conectar e Carregar Dados"

## Exemplo de URL

```
https://docs.google.com/spreadsheets/d/146PCK64ufCpyQ5VM3l8dZ6RFwOo6c7Ew_1D2zKqvVA4/edit?gid=94752619#gid=94752619
```

## Funcionalidades

- ✅ Conexão automática com Google Sheets
- ✅ Cache de dados para melhor performance
- ✅ Atualização automática dos dados
- ✅ Interface intuitiva para configuração
- ✅ Fallback para upload manual de arquivos

## Estrutura Esperada da Planilha

A planilha deve conter as seguintes colunas:
- Data
- Sprint
- Time
- Nome da Task
- Link da Task
- Status
- Responsável
- Motivo
- Motivo2
- Motivo3
- Motivo4
- Motivo5
- Motivo6
- Motivo7
- Responsavel pelo teste
- ID
- Erros