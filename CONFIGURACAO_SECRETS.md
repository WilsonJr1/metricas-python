# Configuração de Secrets para Google Sheets

Este projeto utiliza o sistema de secrets do Streamlit para manter as credenciais seguras e não expostas no repositório.

## Configuração Local

1. **Crie a pasta `.streamlit`** na raiz do projeto (se não existir)
2. **Copie o arquivo `secrets_example.toml`** para `.streamlit/secrets.toml`
3. **Edite o arquivo `.streamlit/secrets.toml`** com suas credenciais reais:
   - Substitua `SEU_ID_DA_PLANILHA` pelo ID da sua planilha Google Sheets
   - Substitua `NOME_DA_ABA` pelo nome da aba que contém os dados
   - Preencha todas as credenciais da conta de serviço do Google

## Obtendo Credenciais do Google

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API do Google Sheets e Google Drive
4. Crie uma conta de serviço:
   - Vá em "IAM & Admin" > "Service Accounts"
   - Clique em "Create Service Account"
   - Baixe o arquivo JSON com as credenciais
5. Compartilhe sua planilha com o email da conta de serviço

## Configuração no Streamlit Cloud

Quando fizer deploy no Streamlit Cloud:

1. Vá nas configurações do seu app
2. Na seção "Secrets", cole o conteúdo do seu arquivo `secrets.toml`
3. Salve as configurações

## Segurança

- **NUNCA** commite o arquivo `.streamlit/secrets.toml` no repositório
- Adicione `.streamlit/` ao seu `.gitignore`
- Use apenas o arquivo `secrets_example.toml` como referência

## Estrutura dos Secrets

```toml
[google_sheets]
spreadsheet_url = "URL_DA_PLANILHA"
worksheet_name = "NOME_DA_ABA"
project_id = "seu-projeto-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA\n-----END PRIVATE KEY-----\n"
client_email = "seu-service-account@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

O código foi refatorado para usar `st.secrets` em vez de variáveis hardcoded, garantindo maior segurança.