# Solução de Problemas - Geração de PDFs no Streamlit Cloud

## Problema Identificado
Os gráficos não são gerados nos PDFs quando o aplicativo está em produção no Streamlit Cloud, embora funcionem corretamente em ambiente de homologação local.

## Soluções Implementadas

### 1. Configurações Otimizadas do Kaleido
- **Arquivo**: `streamlit_config.py`
- **Função**: Configurações específicas para Streamlit Cloud
- **Melhorias**:
  - Argumentos do Chromium otimizados para ambiente containerizado
  - Timeout aumentado para 60 segundos
  - Configurações de memória e processo único

### 2. Função de Exportação Robusta
- **Arquivo**: `dashboard.py` - função `exportar_grafico_para_pdf()`
- **Melhorias**:
  - Múltiplas estratégias de conversão (PNG, JPEG)
  - Fallbacks automáticos entre engines (kaleido, orca)
  - Configurações específicas para Streamlit Cloud
  - Timeouts configuráveis por estratégia
  - Último recurso com configurações mínimas

### 3. Diagnóstico Integrado
- **Localização**: Sidebar do dashboard
- **Funcionalidades**:
  - Detecção automática do ambiente (Streamlit Cloud, local, etc.)
  - Verificação de dependências (Kaleido, ReportLab)
  - Teste de funcionalidade de geração de gráficos
  - Relatório de problemas encontrados

## Como Usar o Diagnóstico

1. **Acesse o Dashboard**: Abra o aplicativo no Streamlit Cloud
2. **Sidebar**: Procure por "🔍 Diagnóstico do Sistema" na barra lateral
3. **Execute o Diagnóstico**: Clique em "Executar Diagnóstico"
4. **Teste Gráficos**: Use "Testar Geração de Gráfico" para verificar funcionalidade

## Problemas Conhecidos e Soluções

### Problema: Kaleido trava no Streamlit Cloud
**Solução**: Configurações específicas do Chromium implementadas
```python
# Argumentos seguros para produção
safe_args = [
    "--single-process",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--no-first-run",
    "--disable-default-apps"
]
```

### Problema: Timeout na geração de imagens
**Solução**: Múltiplas estratégias com timeouts escalonados
- Kaleido PNG: 30 segundos
- Kaleido JPEG: 20 segundos  
- Orca PNG: 15 segundos
- Configurações mínimas: sem timeout

### Problema: Imagens vazias ou corrompidas
**Solução**: Verificação de tamanho mínimo (>100 bytes) e fallbacks

## Monitoramento

### Logs de Diagnóstico
Todos os passos de conversão são logados:
```
Kaleido versão: 0.2.1
Configurações Chromium aplicadas para 'Nome do Gráfico'
Tentando converter 'Nome do Gráfico' com kaleido (png)...
Sucesso: Gráfico 'Nome do Gráfico' convertido com kaleido (png)
```

### Indicadores de Status
- ✅ Verde: Funcionando corretamente
- ❌ Vermelho: Problema identificado
- ⚠️ Amarelo: Aviso ou configuração subótima

## Dependências Necessárias

Verifique se estão no `requirements.txt`:
```
streamlit>=1.28.0
plotly>=5.15.0
kaleido>=0.2.1
reportlab>=3.6.0
```

## Contato para Suporte

Se os problemas persistirem após implementar essas soluções:
1. Execute o diagnóstico completo
2. Capture os logs de erro
3. Documente o ambiente específico (Streamlit Cloud vs local)
4. Reporte com detalhes técnicos coletados

## Atualizações Futuras

Este sistema de diagnóstico pode ser expandido para:
- Monitoramento automático de performance
- Alertas proativos de problemas
- Métricas de sucesso de geração de PDFs
- Otimizações baseadas em uso real