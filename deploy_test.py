import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_production import aplicar_configuracoes_producao
from dashboard import exportar_grafico_para_pdf
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
from datetime import datetime

st.set_page_config(
    page_title="Teste de Deploy - Gráficos PDF",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Teste de Deploy - Gráficos em PDF")
st.markdown("---")

if st.button("🧪 Executar Teste Completo", type="primary"):
    with st.spinner("Executando testes..."):
        try:
            st.subheader("1️⃣ Configurações de Produção")
            aplicar_configuracoes_producao()
            st.success("✅ Configurações aplicadas")
            
            st.subheader("2️⃣ Criação do Gráfico")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[10, 11, 12, 13, 14],
                mode='lines+markers',
                name='Teste Deploy',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Gráfico de Teste - Deploy Streamlit Cloud",
                xaxis_title="Período",
                yaxis_title="Valores",
                template="plotly_white",
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.success("✅ Gráfico criado")
            
            st.subheader("3️⃣ Conversão Ultra-Robusta")
            resultado_img = exportar_grafico_para_pdf(fig, "Teste Deploy Streamlit Cloud")
            
            if resultado_img:
                st.success(f"✅ Conversão bem-sucedida: {type(resultado_img)}")
                
                st.subheader("4️⃣ Geração do PDF")
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                story.append(Paragraph("Teste de Deploy - Streamlit Cloud", styles['Title']))
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph("Gráfico de Teste:", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                story.append(resultado_img)
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("✅ Se você consegue ver o gráfico acima, a solução ultra-robusta funcionou!", styles['Normal']))
                
                doc.build(story)
                pdf_bytes = buffer.getvalue()
                buffer.close()
                
                st.success(f"✅ PDF gerado com sucesso: {len(pdf_bytes)} bytes")
                
                st.download_button(
                    label="📥 Baixar PDF de Teste",
                    data=pdf_bytes,
                    file_name=f"teste_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
                
                st.balloons()
                st.success("🎉 TESTE CONCLUÍDO COM SUCESSO!")
                
            else:
                st.error("❌ Falha na conversão do gráfico")
                
        except Exception as e:
            st.error(f"❌ Erro durante o teste: {str(e)}")
            st.code(str(e))

st.markdown("---")
st.markdown("""
### 📋 Instruções para Teste no Streamlit Cloud:

1. **Deploy este arquivo** junto com sua aplicação
2. **Acesse a URL** do Streamlit Cloud
3. **Execute o teste** clicando no botão acima
4. **Verifique se o PDF** contém o gráfico
5. **Compare com o comportamento local**

### 🔍 O que este teste verifica:
- ✅ Configurações de produção aplicadas
- ✅ Criação de gráficos Plotly
- ✅ Conversão ultra-robusta para imagem
- ✅ Geração de PDF com gráfico
- ✅ Download do arquivo final

### 🚨 Se o teste falhar:
- Verifique os logs do Streamlit Cloud
- Confirme se todas as dependências estão instaladas
- Verifique se o arquivo `requirements.txt` está atualizado
""")