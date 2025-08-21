import os
import sys

def setup_production_environment():
    """
    Configura o ambiente de produção para o Streamlit Cloud
    Usando as novas configurações do plotly.io.defaults
    """
    print("🔧 Configurando ambiente para produção...")
    
    # Configurações de ambiente críticas
    os.environ['MPLBACKEND'] = 'Agg'
    os.environ['DISPLAY'] = ':99'
    os.environ['KALEIDO_DISABLE_GPU'] = 'true'
    os.environ['CHROMIUM_FLAGS'] = '--no-sandbox --disable-dev-shm-usage --disable-gpu --single-process'
    
    try:
        # Configurar Plotly/Kaleido
        import plotly.io as pio
        
        # CONFIGURAÇÕES DO KALEIDO (NOVA API)
        try:
            # Tentar usar a nova API do plotly.io.defaults
            if hasattr(pio, 'defaults'):
                pio.defaults.chromium_args = (
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                )
                pio.defaults.default_timeout = 60
                print("✅ Configurações aplicadas via plotly.io.defaults")
            else:
                # Fallback para API antiga (com warning)
                pio.kaleido.scope.chromium_args = (
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                )
                pio.kaleido.scope.default_timeout = 60
                print("⚠️ Usando API depreciada do kaleido.scope")
        except Exception as config_error:
            print(f"⚠️ Erro nas configurações do Kaleido: {config_error}")
        
        print("✅ Configurações de produção aplicadas com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar produção: {e}")
        return False

def verify_dependencies():
    """
    Verifica se todas as dependências estão disponíveis
    """
    required_modules = ['streamlit', 'plotly', 'kaleido', 'reportlab', 'pandas']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} disponível")
        except ImportError:
            missing.append(module)
            print(f"❌ {module} não encontrado")
    
    return len(missing) == 0, missing

if __name__ == "__main__":
    print("=== CONFIGURAÇÃO DE PRODUÇÃO ===")
    setup_production_environment()
    deps_ok, missing = verify_dependencies()
    
    if deps_ok:
        print("🎉 Ambiente configurado e pronto para produção!")
    else:
        print(f"⚠️ Dependências faltando: {missing}")