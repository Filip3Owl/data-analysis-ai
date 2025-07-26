import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO

def generate_visualization(data, chart_type="auto"):
    """Gera visualizações dos dados"""
    if isinstance(data, str):
        try:
            data = pd.read_json(StringIO(data))
        except:
            return None
    
    if data.empty:
        return None
    
    fig, ax = plt.subplots()
    
    if chart_type == "pie":
        data.plot.pie(y=data.columns[1], ax=ax)
    elif chart_type == "bar":
        data.plot.bar(x=data.columns[0], ax=ax)
    elif chart_type == "table":
        ax.axis('off')
        ax.table(
            cellText=data.values,
            colLabels=data.columns,
            loc='center'
        )
    
    plt.tight_layout()
    return fig

def detect_chart_type(user_input):
    """Detecta o tipo de visualização solicitada"""
    user_input = user_input.lower()
    if "gráfico" in user_input or "grafico" in user_input:
        if "pizza" in user_input:
            return "pie"
        return "bar"
    elif "tabela" in user_input:
        return "table"
    return "text"