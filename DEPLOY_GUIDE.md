# 🚀 Guia de Deploy - Correção de Imagens em PDFs

## 🔍 Problema Identificado

Quando o projeto é deployado no Streamlit Cloud, os PDFs são gerados **sem as imagens dos gráficos**, mesmo funcionando corretamente no ambiente local.

## 🎯 Causa Raiz

O **Kaleido v1** (usado pelo Plotly para gerar imagens) requer que o **Chrome/Chromium** esteja instalado no servidor. No Streamlit Cloud, isso não vem por padrão.

## ✅ Solução Implementada

### 1. **Arquivo `packages.txt`** (CRÍTICO)

```txt
chromium-browser
chromium-chromedriver
xvfb
```

**Este arquivo é ESSENCIAL** - ele instrui o Streamlit Cloud a instalar o Chrome durante o deploy.

### 2. **Configuração `.streamlit/config.toml`**

```toml
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false

[theme]
base = "light"
```

### 3. **Configurações de Produção Aprimoradas**

O arquivo `config_production.py` foi atualizado para:
- ✅ Detectar automaticamente o Chrome instalado
- ✅ Configurar variáveis de ambiente adequadas
- ✅ Aplicar flags de segurança necessárias

## 📋 Checklist de Deploy

### ✅ **Arquivos Obrigatórios**
- [ ] `packages.txt` (com chromium-browser)
- [ ] `.streamlit/config.toml`
- [ ] `requirements.txt` (com kaleido>=0.2.1)
- [ ] `config_production.py` (configurações atualizadas)

### ✅ **Configurações do Streamlit Cloud**
1. **Repository**: Seu repositório GitHub
2. **Branch**: main
3. **Main file**: `dashboard.py`
4. **Secrets**: Configure `.streamlit/secrets.toml` com credenciais do Google Sheets

## 🔧 Verificação Pós-Deploy

### **Teste de Diagnóstico**
1. Acesse o dashboard deployado
2. Abra a sidebar → "🔍 Diagnóstico do Sistema"
3. Clique em "Executar Diagnóstico"
4. Verifique se aparece: **"✅ Kaleido v[versão]"**
5. Clique em "Testar Geração de Gráfico"
6. Deve aparecer: **"✅ Teste de gráfico bem-sucedido"**

### **Teste de PDF**
1. Gere qualquer relatório em PDF
2. Verifique se as imagens dos gráficos aparecem corretamente

## 🚨 Troubleshooting

### **Se ainda não funcionar:**

1. **Verifique os logs do Streamlit Cloud**:
   - Procure por erros relacionados a "kaleido", "chrome" ou "chromium"

2. **Mensagens de erro comuns**:
   - `"Chrome not found"` → Verifique se `packages.txt` está no repositório
   - `"Kaleido timeout"` → Problema de configuração do Chrome
   - `"Permission denied"` → Flags de segurança não aplicadas

3. **Forçar reinstalação**:
   - Faça um commit vazio para triggerar novo deploy
   - Verifique se todos os arquivos estão commitados

## 📞 Suporte

Se o problema persistir:
1. Execute o diagnóstico e anote as mensagens
2. Verifique os logs do Streamlit Cloud
3. Confirme que todos os arquivos estão no repositório GitHub

---

**✅ Com essas configurações, as imagens dos gráficos devem aparecer corretamente nos PDFs em produção!**