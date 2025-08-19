
# Dashboard de Métricas DelTech - QA & Sustentação

Dashboard interativo para análise de métricas de qualidade e performance da equipe de Q.A e sustentação.

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

## 🚀 Deploy no Streamlit Cloud (Recomendado)

### Pré-requisitos:
1. Conta no [GitHub](https://github.com)
2. Conta no [Streamlit Cloud](https://share.streamlit.io)

### Passos para Deploy:

1. **Faça fork ou clone este repositório**
2. **Acesse [share.streamlit.io](https://share.streamlit.io)**
3. **Conecte sua conta GitHub**
4. **Clique em "New app"**
5. **Selecione:**
   - Repository: `seu-usuario/dashboard-qa-deltech`
   - Branch: `main`
   - Main file path: `dashboard.py`
6. **Clique em "Deploy!"**

✅ **Pronto!** Seu dashboard estará online em poucos minutos.

## 💻 Execução Local

### Instalação:
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/dashboard-qa-deltech.git
cd dashboard-qa-deltech

# Instale as dependências
pip install -r requirements.txt
```

### Executar:
```bash
streamlit run dashboard.py
```

O dashboard estará disponível em: `http://localhost:8501`

## 📋 Como Usar

1. **Acesse o dashboard** (online ou local)
2. **Faça upload** da sua planilha Excel usando o botão "Escolha o arquivo Excel"
3. **Explore as métricas** na parte superior da página
4. **Use os filtros** na barra lateral para análises específicas
5. **Visualize os gráficos** interativos para insights detalhados



## Exemplo de Uso

Se você tem uma planilha `dados.xlsx` com as colunas:
```
Data       | Nome    | Valor
15/01/2025 | Item A  | 100
30/01/2025 | Item B  | 200
```

Após executar o script, será criado `dados_com_sprint.xlsx`:
```
Data       | Nome    | Valor | Sprint
15/01/2025 | Item A  | 100   | Sprint 1
30/01/2025 | Item B  | 200   | Sprint 2
```

**Nota**: O cálculo considera apenas dias úteis (segunda a sexta-feira). Datas que caem em finais de semana não pertencem a nenhuma sprint.

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

## 📁 Estrutura do Projeto

```
📁 dashboard-qa-deltech/
├── 📄 dashboard.py           # 🎯 Aplicação principal do dashboard
├── 📄 requirements.txt       # 📦 Dependências Python
├── 📄 README.md             # 📖 Documentação do projeto
└── 📄 .gitignore            # 🚫 Arquivos ignorados pelo Git
```

## Estrutura de Dados

O dashboard espera um arquivo Excel com as seguintes colunas:

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
- **Motivo4**: Quarto motivo (se rejeitada)
- **Motivo5**: Quinto motivo (se rejeitada)
- **Motivo6**: Sexto motivo (se rejeitada)
- **Motivo7**: Sétimo motivo (se rejeitada)
- **Responsavel pelo teste**: Testador responsável
- **ID**: Identificador único da task

## 📋 Formato da Planilha

Sua planilha Excel deve conter as seguintes colunas:

| Coluna | Descrição | Obrigatória |
|--------|-----------|-------------|
| **Data** | Data da task | ✅ |
| **Sprint** | Sprint da task | ✅ |
| **Time** | Time responsável | ✅ |
| **Nome da Task** | Descrição da task | ✅ |
| **Status** | Status atual (APROVADA/REJEITADA) | ✅ |
| **Responsavel pelo teste** | Quem testou (Eduardo/Wilson) | ✅ |
| **Motivo** | Motivo da rejeição | ⚠️ |
| **Link da task** | URL da task | ⚠️ |
| **ID** | Identificador único | ⚠️ |

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. **Fork** este repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. **Push** para a branch (`git push origin feature/nova-feature`)
5. **Abra** um Pull Request

## 📞 Suporte

Para dúvidas ou problemas:
- 🐛 Abra uma [issue no GitHub](https://github.com/seu-usuario/dashboard-qa-deltech/issues)
- 📧 Entre em contato com a equipe DelTech

## 🔧 Troubleshooting

### ❌ Problemas Comuns:

**Erro "streamlit não encontrado":**
```bash
pip install streamlit
# ou
python -m pip install streamlit
```

**Erro ao ler Excel:**
```bash
pip install openpyxl
```

**Erro de dependências:**
```bash
pip install -r requirements.txt --upgrade
```

**Dashboard não abre localmente:**
- Verifique se a porta 8501 está livre
- Tente acessar manualmente: `http://localhost:8501`
- Use `python -m streamlit run dashboard.py` no Windows

**Problemas com upload de arquivo:**
- Verifique se o arquivo Excel não está aberto em outro programa
- Certifique-se de que o arquivo contém as colunas obrigatórias
- Tamanho máximo recomendado: 200MB

## 📈 Roadmap

- [ ] 🔄 Atualização automática de dados
- [ ] 📊 Novos tipos de gráficos
- [ ] 🎨 Temas personalizáveis
- [ ] 📱 App mobile nativo
- [ ] 🔗 Integração com APIs
- [ ] 📧 Relatórios por email

## 📄 Licença

Este projeto é de uso interno da DelTech para análise de dados de Q.A.

---

**🚀 Desenvolvido com ❤️ para otimizar a análise de dados de Q.A da DelTech**

*Última atualização: Janeiro 2025*