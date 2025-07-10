import pandas as pd
from datetime import datetime, timedelta
import random

# Criar dados de exemplo
data_exemplo = {
    'Data': [datetime.now() - timedelta(days=random.randint(1, 30)) for _ in range(50)],
    'Sprint': [f'Sprint {random.randint(1, 5)}' for _ in range(50)],
    'Time': [random.choice(['Frontend', 'Backend', 'Mobile', 'DevOps']) for _ in range(50)],
    'Nome da Task': [f'Task {i+1}' for i in range(50)],
    'Link da Task': [f'https://jira.com/task-{i+1}' for i in range(50)],
    'Status': [random.choice(['APROVADA', 'REJEITADA', 'PRONTO PARA PUBLICACAO']) for _ in range(50)],
    'Responsavel': [random.choice(['Joao', 'Maria', 'Pedro', 'Ana', 'Carlos']) for _ in range(50)],
    'Motivo': [random.choice(['Bug encontrado', 'Aprovada', 'Sem teste', 'Erro de layout']) for _ in range(50)],
    'Motivo2': [random.choice(['', 'Performance', 'Usabilidade', 'Funcionalidade']) for _ in range(50)],
    'Motivo3': [random.choice(['', 'Critico', 'Menor', 'Medio']) for _ in range(50)],
    'Responsavel pelo teste': [random.choice(['Eduardo', 'Wilson', '']) for _ in range(50)],
    'ID': [f'ID-{i+1:03d}' for i in range(50)]
}

df = pd.DataFrame(data_exemplo)
df.to_excel('dados_exemplo.xlsx', index=False)
print('Arquivo dados_exemplo.xlsx criado com sucesso!')