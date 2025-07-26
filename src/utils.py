import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO
import numpy as np

def generate_visualization(data, chart_type="auto", title=None):
    """
    Gera visualizações dos dados com tratamento robusto
    
    Parâmetros:
        data (pd.DataFrame/str): Dados a serem plotados (DataFrame ou JSON string)
        chart_type (str): Tipo de gráfico ('auto', 'pie', 'bar', 'line', 'table')
        title (str): Título opcional para o gráfico
    
    Retorna:
        matplotlib.figure.Figure ou None em caso de erro
    """
    # Conversão de string JSON para DataFrame
    if isinstance(data, str):
        try:
            data = pd.read_json(StringIO(data))
        except Exception as e:
            print(f"Erro ao converter JSON: {str(e)}")
            return None
    
    # Verificação de dados vazios
    if data.empty or not isinstance(data, pd.DataFrame):
        print("Dados vazios ou formato inválido")
        return None
    
    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Determinação automática do tipo de gráfico
        if chart_type == "auto":
            chart_type = _determine_best_chart_type(data)
        
        # Geração dos gráficos
        if chart_type == "pie":
            if len(data.columns) >= 2:
                data.plot.pie(
                    y=data.columns[1], 
                    ax=ax,
                    autopct='%1.1f%%',
                    startangle=90
                )
                ax.set_ylabel('')
            else:
                print("Dados insuficientes para gráfico de pizza")
                return None
                
        elif chart_type == "bar":
            if len(data.columns) >= 2:
                data.plot.bar(
                    x=data.columns[0],
                    y=data.columns[1],
                    ax=ax,
                    rot=45 if len(data) > 5 else 0
                )
            else:
                data.plot.bar(ax=ax)
                
        elif chart_type == "line":
            if len(data.columns) >= 2:
                data.plot.line(
                    x=data.columns[0],
                    y=data.columns[1:],
                    ax=ax,
                    marker='o'
                )
            else:
                data.plot.line(ax=ax)
                
        elif chart_type == "table":
            ax.axis('off')
            table = ax.table(
                cellText=data.values,
                colLabels=data.columns,
                loc='center',
                cellLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
        
        # Configurações comuns
        if title:
            ax.set_title(title)
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Erro ao gerar visualização: {str(e)}")
        return None

def _determine_best_chart_type(data):
    """Determina o melhor tipo de gráfico com base nos dados"""
    if len(data.columns) == 1:
        return "table"
    
    # Para 2 colunas
    if len(data.columns) == 2:
        if pd.api.types.is_numeric_dtype(data.iloc[:, 1]):
            if len(data) <= 7:
                return "pie"
            return "bar"
        return "table"
    
    # Para múltiplas colunas numéricas
    return "line"

def detect_chart_type(user_input):
    """
    Detecta o tipo de visualização solicitada pelo usuário
    
    Parâmetros:
        user_input (str): Texto de entrada do usuário
    
    Retorna:
        str: Tipo de gráfico ('pie', 'bar', 'line', 'table', 'text')
    """
    if not isinstance(user_input, str):
        return "text"
        
    user_input = user_input.lower()
    
    # Mapeamento de termos para tipos de gráfico
    chart_mapping = {
        'pizza': 'pie',
        'setor': 'pie',
        'barras': 'bar',
        'colunas': 'bar',
        'linhas': 'line',
        'temporal': 'line',
        'tabela': 'table',
        'lista': 'table'
    }
    
    # Verifica termos específicos primeiro
    for term, chart_type in chart_mapping.items():
        if term in user_input:
            return chart_type
    
    # Fallback para termos genéricos
    if "gráfico" in user_input or "grafico" in user_input:
        return "bar"
    elif "visualizar" in user_input or "mostrar" in user_input:
        return "auto"
        
    return "text"