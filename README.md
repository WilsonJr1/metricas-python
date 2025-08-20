
# 📊 Dashboard de Métricas DelTech - QA & Sustentação

Dashboard interativo desenvolvido em Streamlit para análise de métricas de qualidade e performance das equipes de Q.A e Sustentação da DelTech.

## 🚀 Início Rápido

1. **Clone o repositório**
2. **Instale as dependências**: `pip install -r requirements.txt`
3. **Execute o dashboard**: `streamlit run dashboard.py`
4. **Acesse**: http://localhost:8501

## 📁 Estrutura do Projeto

```
📁 metricas-python/
├── 📄 dashboard.py              # 🎯 Dashboard principal
├── 📄 analisar_bugs.py          # 🐛 Análise de bugs
├── 📄 analisar_planilhas.py     # 📊 Processamento de planilhas
├── 📄 sustentacao.py            # 🔧 Métricas de sustentação
├── 📄 ler_bugs.py               # 📖 Leitura de dados de bugs
├── 📄 google_sheets_integration.py # 🔗 Integração Google Sheets
├── 📄 requirements.txt          # 📦 Dependências
├── 📄 secrets_example.toml      # 🔐 Exemplo de configuração
└── 📄 README.md                 # 📖 Documentação
```

## Funcionalidades

### 🔍 Módulo de Qualidade (QA)

#### 🎯 Visão Geral Estratégica
- Evolução da qualidade ao longo do tempo
- Distribuição de status das tasks
- Análise de erros por time
- Taxa de rejeição por time

#### 🛡️ Prevenção e Qualidade
- Bugs identificados por time
- Distribuição de bugs por time
- Tipos de falha mais comuns
- Motivos de rejeição
- Taxa de aprovação vs rejeição
- Análise por desenvolvedor
- Evolução da taxa de qualidade

#### 📊 Visão por Sprint
- Timeline de tasks testadas
- Cobertura de QA por time

#### 👤 Visão por Testador
- Estatísticas individuais de performance
- Comparativo entre testadores
- Ranking de performance

#### 📋 Tarefas Sem Teste
- Análise de tasks não testadas
- Filtros por sprint, time e responsável
- Métricas de impacto na cobertura

### 🔧 Módulo de Sustentação

#### 📈 Análise de Velocidade
- Velocidade planejada vs real por sprint
- Desvio da velocidade
- Tendências de performance do time

#### 👥 Análise por Desenvolvedor
- Horas trabalhadas por desenvolvedor
- Distribuição de tarefas por tipo e status
- Estatísticas individuais de produtividade

#### ⏱️ Gestão de Tempo
- Análise de desvios entre horas estimadas e trabalhadas
- Timeline de tarefas por desenvolvedor
- Identificação de maiores desvios e economias

#### 📊 Métricas Executivas
- Velocidade média do time
- Total de horas trabalhadas
- Desvio médio de estimativas
- Desenvolvedores ativos

## 🛠️ Tecnologias

- **Python 3.7+**
- **Streamlit** - Framework web para aplicações de dados
- **Plotly** - Biblioteca para gráficos interativos
- **OpenPyXL** - Leitura de arquivos Excel
- **NumPy** - Computação numérica
- **Google Sheets API** - Integração com planilhas online

## 🔗 Configuração Google Sheets

### 1. Criar Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou selecione um existente
3. Ative a **Google Sheets API**
4. Crie uma **Service Account** em "APIs & Services" > "Credentials"
5. Baixe o arquivo JSON das credenciais

### 2. Configurar Secrets

1. Copie `secrets_example.toml` para `.streamlit/secrets.toml`
2. Preencha com suas credenciais reais:

```toml
[google_sheets]
spreadsheet_url = "URL_DA_SUA_PLANILHA"
worksheet_name = "NOME_DA_ABA"
project_id = "seu-projeto-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE\n-----END PRIVATE KEY-----\n"
client_email = "service-account@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

### 3. Compartilhar Planilha

1. Abra sua planilha no Google Sheets
2. Clique em "Compartilhar"
3. Adicione o email da Service Account
4. Dê permissão de "Visualizador"

⚠️ **Importante**: Nunca commite o arquivo `.streamlit/secrets.toml` no repositório!

## 🚀 Deploy no Streamlit Cloud

1. **Fork** este repositório no GitHub
2. **Acesse** [share.streamlit.io](https://share.streamlit.io)
3. **Conecte** sua conta GitHub
4. **Crie novo app** selecionando:
   - Repository: `seu-usuario/metricas-python`
   - Branch: `main`
   - Main file path: `dashboard.py`
5. **Configure secrets** nas configurações do app
6. **Deploy!** 🎉

## 💻 Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/metricas-python.git
cd metricas-python

# Instale as dependências
pip install -r requirements.txt

# Execute o dashboard
streamlit run dashboard.py
```

**Acesse**: http://localhost:8501

## 📋 Como Usar

1. **Acesse o dashboard** (online ou local)
2. **Conecte ao Google Sheets** ou **faça upload** de arquivo Excel
3. **Explore as métricas** na parte superior
4. **Use os filtros** na barra lateral
5. **Visualize os gráficos** interativos

### 📊 Dados Suportados

O dashboard processa planilhas com as seguintes colunas:

| Coluna | Descrição | Obrigatória |
|--------|-----------|-------------|
| **Data** | Data da task | ✅ |
| **Sprint** | Sprint da task | ✅ |
| **Time** | Time responsável | ✅ |
| **Nome da Task** | Descrição da task | ✅ |
| **Status** | APROVADA/REJEITADA/PRONTO PARA PUBLICAÇÃO | ✅ |
| **Responsavel pelo teste** | Testador (Eduardo/Wilson) | ✅ |
| **Motivo** | Motivo da rejeição | ⚠️ |
| **Link da task** | URL da task | ⚠️ |
| **ID** | Identificador único | ⚠️ |

## 📊 Métricas Disponíveis

### 🔢 Métricas Principais:
- **📊 Total na Planilha**: Número total de registros carregados
- **✅ Testes Efetuados**: Tasks testadas por Eduardo e Wilson
- **⚠️ Sem Teste**: Tasks que não passaram por teste de Q.A
- **🚫 Bugs Identificados**: Tasks rejeitadas (problemas detectados)

### 📈 Gráficos Interativos:
1. **📊 Tasks por Sprint**: Distribuição de tasks ao longo das sprints
2. **✅ Status das Tasks**: Proporção de aprovadas vs rejeitadas
3. **📅 Timeline de Tasks**: Evolução temporal das tasks
4. **🔥 Heatmap Sprint vs Status**: Correlação entre sprints e status
5. **📋 Top Motivos de Rejeição**: Principais causas de bugs identificados
6. **👤 Performance por Responsável**: Análise individual de testadores

## 🎯 Filtros Disponíveis

- **📅 Período**: Filtrar por intervalo de datas específico
- **🏃 Sprint**: Selecionar uma ou múltiplas sprints
- **👤 Responsável pelo Teste**: Filtrar por testador (Eduardo/Wilson)
- **📊 Status**: Filtrar por status das tasks (Aprovada/Rejeitada)

## 🎯 Filtros Disponíveis

- **📅 Período**: Filtrar por intervalo de datas
- **🏃 Sprint**: Selecionar sprints específicas
- **👤 Responsável pelo Teste**: Filtrar por testador
- **📊 Status**: Filtrar por status das tasks
- **🏢 Time**: Filtrar por time responsável

## 🔧 Troubleshooting

### Problemas Comuns:

**Erro de dependências:**
```bash
pip install -r requirements.txt --upgrade
```

**Dashboard não abre:**
- Verifique se a porta 8501 está livre
- Use: `python -m streamlit run dashboard.py`

**Problemas com Google Sheets:**
- Verifique se a Service Account tem acesso à planilha
- Confirme se as credenciais estão corretas no `secrets.toml`

## 📞 Suporte

Para dúvidas ou problemas, entre em contato com a equipe DelTech.

---

**🚀 Desenvolvido com ❤️ para otimizar a análise de dados de Q.A da DelTech**

*Última atualização: Agosto 2025*