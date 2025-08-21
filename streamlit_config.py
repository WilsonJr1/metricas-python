import os
import plotly.io as pio

def configure_plotly_for_streamlit():
    """
    Configuração DEFINITIVA e MINIMALISTA para Streamlit Cloud
    Apenas o essencial que FUNCIONA
    """
    try:
        # Configurações de ambiente obrigatórias
        os.environ['MPLBACKEND'] = 'Agg'
        os.environ['DISPLAY'] = ':99'
        
        # Configurar Kaleido com o mínimo necessário
        pio.kaleido.scope.chromium_args = (
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--single-process'
        )
        pio.kaleido.scope.default_timeout = 60
        
        print("✅ Configurações minimalistas aplicadas para Streamlit Cloud")
        
    except Exception as e:
        print(f"⚠️ Erro ao configurar Plotly: {e}")

def test_kaleido_functionality():
    """
    Teste simples do Kaleido
    """
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Bar(x=['A', 'B'], y=[1, 2]))
        fig.update_layout(title="Teste", width=400, height=300)
        
        img_bytes = fig.to_image(format="png", width=400, height=300)
        
        if img_bytes and len(img_bytes) > 100:
            print(f"✅ Kaleido OK: {len(img_bytes)} bytes")
            return True
        else:
            print(f"❌ Kaleido falhou: {len(img_bytes) if img_bytes else 0} bytes")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    configure_plotly_for_streamlit()
    test_kaleido_functionality()