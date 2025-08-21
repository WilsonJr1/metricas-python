import os
import plotly.io as pio

def configure_plotly_for_streamlit():
    """
    Configurações específicas para otimizar Plotly/Kaleido no Streamlit Cloud
    """
    try:
        # Configurar variáveis de ambiente para Streamlit Cloud
        os.environ['KALEIDO_USE_SWIFT'] = 'false'
        os.environ['PLOTLY_RENDERER'] = 'browser'
        
        # Configurações do Kaleido para produção
        if hasattr(pio, 'kaleido'):
            # Timeout mais longo para produção
            pio.kaleido.scope.default_timeout = 60
            
            # Configurações de Chromium otimizadas para Streamlit Cloud
            chromium_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--single-process',
                '--no-first-run',
                '--memory-pressure-off'
            ]
            
            pio.kaleido.scope.chromium_args = tuple(chromium_args)
            
            print("Configurações Plotly/Kaleido aplicadas para Streamlit Cloud")
            return True
            
    except Exception as e:
        print(f"Erro ao configurar Plotly para Streamlit: {e}")
        return False
    
    return False

def test_kaleido_functionality():
    """
    Testa se o Kaleido está funcionando corretamente
    """
    try:
        import plotly.graph_objects as go
        import kaleido
        
        print(f"Testando Kaleido versão: {kaleido.__version__}")
        
        # Criar um gráfico simples para teste
        fig = go.Figure(data=go.Bar(x=['A', 'B', 'C'], y=[1, 2, 3]))
        fig.update_layout(
            title="Teste Kaleido",
            width=400,
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Tentar converter para imagem
        img_bytes = fig.to_image(format="png", width=400, height=300)
        
        if img_bytes and len(img_bytes) > 100:
            print("✅ Kaleido está funcionando corretamente")
            return True
        else:
            print("❌ Kaleido não está gerando imagens válidas")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do Kaleido: {e}")
        return False

if __name__ == "__main__":
    configure_plotly_for_streamlit()
    test_kaleido_functionality()