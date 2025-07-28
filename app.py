import sys
import os
from pathlib import Path
import streamlit as st
from src.agents import AgentsManager
from src.database import DatabaseManager
from langchain.llms import OpenAI
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import plotly.express as px
import matplotlib.pyplot as plt

# Configuração de caminhos
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

# Configuração inicial
load_dotenv()
st.set_page_config(
    page_title="Analytics com IA - Completo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações de estilo para gráficos
plt.rcParams['text.color'] = '#f8fafc'
plt.rcParams['axes.labelcolor'] = '#f8fafc'
plt.rcParams['xtick.color'] = '#f8fafc'
plt.rcParams['ytick.color'] = '#f8fafc'
plt.rcParams['axes.facecolor'] = '#1a202c'
plt.rcParams['figure.facecolor'] = '#1a202c'

# CSS customizado melhorado com cores mais visíveis para fundo escuro
st.markdown("""
<style>
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --dark-bg: #1a202c;
        --light-text: #f8fafc;
        --medium-text: #e2e8f0;
        --dark-text: #2d3748;
        --card-bg: #2d3748;
        --container-bg: #2d3748;
        --sidebar-bg: #1a202c;
        --schema-bg: #374151;
        --border-color: #4a5568;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --accent: #3182ce;
    }

    body {
        background-color: var(--dark-bg);
        font-family: 'Inter', sans-serif;
        color: var(--light-text);
    }

    .main-header {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: var(--light-text);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    .input-container {
        background-color: var(--container-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
        color: var(--light-text);
    }

    .output-container {
        background-color: var(--container-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
        color: var(--light-text);
    }

    .summary-container {
        background-color: var(--card-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        margin-bottom: 1rem;
        color: var(--light-text);
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .summary-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .summary-icon {
        font-size: 1.5rem;
        margin-right: 0.75rem;
        color: var(--primary);
    }

    .summary-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--light-text);
    }

    .summary-content {
        line-height: 1.6;
        color: var(--light-text);
        font-size: 0.95rem;
    }

    .summary-highlight {
        background-color: #e0e7ff;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-weight: 500;
        color: var(--dark-text);
    }

    .metrics-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        flex: 1;
        background-color: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        color: var(--light-text);
    }

    .insight-box {
        background: #374151;
        padding: 1.25rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        margin: 1rem 0;
        color: var(--light-text);
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        line-height: 1.6;
    }

    .table-container {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        margin: 1rem 0;
        background-color: var(--card-bg);
    }

    .sort-controls {
        background-color: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
        color: var(--light-text);
    }

    .limit-controls {
        background-color: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
        color: var(--light-text);
    }

    .dataframe {
        width: 100% !important;
        color: var(--light-text) !important;
    }

    .dataframe th {
        background-color: var(--primary) !important;
        color: white !important;
        position: sticky;
        top: 0;
        font-weight: 600;
    }

    .dataframe td {
        color: var(--light-text) !important;
        background-color: var(--card-bg) !important;
    }

    .stButton>button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        margin-top: 1rem;
        transition: all 0.3s ease;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .stButton>button:hover {
        background-color: #5a67d8;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
    }

    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 2px 3px rgba(0,0,0,0.3);
    }

    .stButton>button:disabled {
        background-color: #4a5568;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

    .error-box {
        background-color: #2d1b1b;
        padding: 1.25rem;
        border-radius: 8px;
        border-left: 4px solid var(--error);
        margin: 1rem 0;
        color: #fca5a5;
    }

    .result-title {
        color: var(--light-text);
        margin-bottom: 0.5rem;
        font-size: 1.5rem;
        font-weight: 700;
    }

    .result-subtitle {
        color: var(--medium-text);
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }

    /* Melhorias para gráficos */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly div {
        color: var(--light-text) !important;
    }

    /* Ajuste para o expander */
    .st-expander {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background-color: var(--card-bg);
    }

    .st-expander .st-expanderHeader {
        color: var(--light-text) !important;
        font-weight: 600;
        background-color: var(--card-bg) !important;
    }

    .st-expander .st-expanderContent {
        color: var(--light-text) !important;
        background-color: var(--card-bg) !important;
    }

    /* Correção para informações do schema */
    .schema-info {
        background: var(--schema-bg) !important;
        padding: 0.8rem !important;
        border-radius: 6px !important;
        margin: 0.4rem 0 !important;
        font-size: 0.9rem !important;
        color: var(--light-text) !important;
        border: 1px solid var(--border-color) !important;
    }

    .schema-info strong {
        color: var(--primary) !important;
        font-weight: 600 !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--sidebar-bg) !important;
    }

    /* Botões da sidebar */
    .stButton button {
        width: 100% !important;
        text-align: left !important;
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
        border: 1px solid var(--border-color) !important;
        margin-bottom: 0.5rem !important;
    }

    .stButton button:hover {
        background-color: var(--primary) !important;
        color: white !important;
        border-color: var(--primary) !important;
    }

    /* Texto da sidebar */
    .css-1d391kg .stMarkdown {
        color: var(--light-text) !important;
    }

    /* Subheaders da sidebar */
    .css-1d391kg h2, .css-1d391kg h3 {
        color: var(--light-text) !important;
    }

    /* Melhorias no texto geral */
    .stMarkdown {
        color: var(--light-text) !important;
    }

    /* Texto do selectbox e outros elementos */
    .stSelectbox label {
        color: var(--light-text) !important;
        font-weight: 500 !important;
    }

    .stTextArea label {
        color: var(--light-text) !important;
        font-weight: 500 !important;
    }

    .stSlider label {
        color: var(--light-text) !important;
        font-weight: 500 !important;
    }

    /* Footer styling */
    .footer {
        margin-top: 3rem;
        padding: 1.5rem 0;
        text-align: center;
        color: var(--medium-text);
        font-size: 0.9rem;
        border-top: 1px solid var(--border-color);
    }

    .footer a {
        color: var(--primary);
        text-decoration: none;
    }

    /* Info boxes com cores mais visíveis */
    .stAlert {
        color: var(--light-text) !important;
    }

    /* Warning box específico para limite */
    .limit-warning {
        background-color: #2d1b0d;
        border: 1px solid #f59e0b;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #fbbf24;
        font-size: 0.9rem;
    }

    .limit-info {
        background-color: #1e293b;
        border: 1px solid var(--accent);
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #60a5fa;
        font-size: 0.9rem;
    }

    .chart-info {
        background-color: #1e293b;
        border: 1px solid var(--primary);
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #60a5fa;
        font-size: 0.9rem;
    }

    /* Melhorar contraste dos elementos do Streamlit */
    .stApp {
        background-color: var(--dark-bg) !important;
        color: var(--light-text) !important;
    }

    /* Headers principais */
    h1, h2, h3, h4, h5, h6 {
        color: var(--light-text) !important;
    }

    /* Inputs de texto */
    .stTextInput > div > div > input {
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
        border-color: var(--border-color) !important;
    }

    .stTextArea > div > div > textarea {
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
        border-color: var(--border-color) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div > select {
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
        border-color: var(--border-color) !important;
    }

    /* Slider */
    .stSlider > div > div > div {
        color: var(--light-text) !important;
    }

    /* Metrics */
    .metric-container {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--light-text) !important;
    }

    /* DataFrames */
    .stDataFrame {
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: var(--card-bg) !important;
        color: var(--light-text) !important;
    }

    /* Sucesso/Info/Warning/Error messages */
    .stSuccess {
        background-color: #1a2e1a !important;
        color: #4ade80 !important;
        border-color: var(--success) !important;
    }

    .stInfo {
        background-color: #1e293b !important;
        color: #60a5fa !important;
        border-color: var(--accent) !important;
    }

    .stWarning {
        background-color: #2d1b0d !important;
        color: #fbbf24 !important;
        border-color: var(--warning) !important;
    }

    .stError {
        background-color: #2d1b1b !important;
        color: #fca5a5 !important;
        border-color: var(--error) !important;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho principal
st.markdown("""
<div class="main-header">
    <h1>📊 Analytics com IA - Versão Completa</h1>
    <p>Obtenha tabelas, gráficos ou resumos textuais conforme sua necessidade</p>
</div>
""", unsafe_allow_html=True)

# Verificação do banco de dados
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'


@st.cache_data
def quick_database_check():
    if not DB_PATH.exists():
        return False, f"Arquivo não encontrado: {DB_PATH}", 0

    if DB_PATH.stat().st_size == 0:
        return False, "Arquivo do banco está vazio", 0

    try:
        with DatabaseManager(str(DB_PATH)) as db:
            health = db.health_check()
            if not health["connected"]:
                return False, "Falha na conexão", 0
            if health["total_records"] == 0:
                return False, "Banco sem dados", 0
            return True, f"✅ {
                health['tables_count']} tabelas, {
                health['total_records']:,} registros", health["total_records"]
    except Exception as e:
        return False, f"Erro: {str(e)}", 0


db_ok, db_message, total_records = quick_database_check()

if not db_ok:
    st.error(f"❌ **Problema no banco de dados**: {db_message}")
    st.stop()
else:
    st.success(db_message)

# Inicialização do sistema
try:
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager(str(DB_PATH))
        if not st.session_state.db.connect():
            st.error("Falha ao conectar ao banco de dados")
            st.stop()
except Exception as e:
    st.error(f"Erro na inicialização: {str(e)}")
    st.stop()

# Sidebar - Configurações
with st.sidebar:
    st.header("⚙️ Configurações")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    key_input = st.text_input(
        "🔑 Chave OpenAI",
        type="password",
        value=openai_key,
        help="Insira sua chave da OpenAI (sk-...)",
        placeholder="sk-..."
    )
    openai_key = key_input or openai_key

    if openai_key:
        if openai_key.startswith('sk-') and len(openai_key) > 20:
            st.success("✅ Chave válida")
            api_configured = True
        else:
            st.error("❌ Chave inválida")
            api_configured = False
    else:
        st.warning("⚠️ Configure sua chave OpenAI")
        api_configured = False

    st.divider()

    # Informações do banco
    st.subheader("📊 Informações do Banco")
    try:
        schema = st.session_state.db.get_database_schema()

        if not schema:
            st.warning("⚠️ Nenhuma tabela encontrada")
        else:
            for table_name, table_info in schema.items():
                with st.expander(f"📋 {table_name} ({table_info.get('count', 0):,} registros)"):
                    st.markdown("**Colunas:**")
                    columns = table_info.get('columns', [])
                    types = table_info.get('types', [])

                    if columns:
                        for i, col in enumerate(columns):
                            col_type = types[i] if i < len(types) else "N/A"
                            st.markdown(f"""
                            <div class='schema-info'>
                                • <strong>{col}</strong> <span style='color: #cbd5e0;'>({col_type})</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma coluna encontrada")

    except Exception as e:
        st.error(f"Erro ao carregar schema: {e}")
        st.write("Tentando diagnóstico alternativo...")
        try:
            tables = st.session_state.db.get_all_tables()
            st.write(f"Tabelas encontradas: {tables}")
        except Exception as e2:
            st.error(f"Erro adicional: {e2}")

# Interface principal
st.header("🎯 Faça sua Análise")

# Container para área de entrada
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)

    st.markdown(
        '<h3 class="result-title">Descreva o que você quer analisar:</h3>',
        unsafe_allow_html=True)

    user_input = st.text_area(
        " ",
        height=100,
        placeholder="Ex: Mostre os 10 clientes que mais compraram em formato de tabela\nEx: Gráfico de barras dos top 5 estados por vendas",
        help="Descreva sua análise em linguagem natural. Ex: 'Top 5 estados com mais vendas', 'Gráfico de barras das vendas por mês'",
        label_visibility="collapsed")

    # Controles na mesma linha
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        # Adicionando seleção de tipo de gráfico com informação clara
        chart_type = st.selectbox(
            "📊 Tipo de gráfico (se solicitar visualização):",
            options=[
                "Barras",
                "Linhas",
                "Pizza",
                "Área",
                "Dispersão"],
            index=0,
            help="IMPORTANTE: Selecione o tipo de gráfico que deseja plotar. Mencione 'gráfico' na sua descrição para usar esta opção.")

        # Informação sobre como usar gráficos
        st.markdown(f"""
        <div class="chart-info">
            💡 <strong>Dica:</strong> Para gerar gráficos, inclua palavras como "gráfico", "chart" ou "visualização" na sua consulta.
            Tipo selecionado: <strong>{chart_type}</strong>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Limite de registros para análise com base no total disponível
        # Usa o total real do banco ou 10k, o menor
        max_records = min(total_records, 10000)
        # Padrão é 1000 ou o máximo disponível
        default_limit = min(1000, max_records)

        record_limit = st.slider(
            f"📄 Limite de registros (máx: {
                max_records:,    }):",
            min_value=10,
            max_value=max_records,
            value=default_limit,
            step=50,
            help=f"Defina quantos registros analisar. Total disponível no banco: {
                total_records:,        }")

    with col3:
        # Mostrar informação sobre o limite com contexto do banco
        percentage = (record_limit / total_records) * \
            100 if total_records > 0 else 0
        st.markdown(f"""
        <div class="limit-info">
            <strong>Analisará:</strong><br>
            {record_limit:,} registros<br>
            <small>({percentage:.1f}% do total)</small>
        </div>
        """, unsafe_allow_html=True)

    # Avisos contextuais sobre o limite
    if record_limit >= total_records:
        st.markdown(f"""
        <div class="limit-info">
            ✅ <strong>Análise Completa:</strong> Você selecionou analisar todos os {total_records:,} registros disponíveis no banco.
        </div>
        """, unsafe_allow_html=True)
    elif record_limit >= max_records * 0.8:  # Aviso quando próximo do limite técnico
        st.markdown(f"""
        <div class="limit-warning">
            ⚠️ <strong>Atenção:</strong> Você selecionou {record_limit:,} registros de {total_records:,} disponíveis.
            Para consultas muito grandes, o processamento pode ser mais lento.
        </div>
        """, unsafe_allow_html=True)
    elif record_limit < total_records * 0.1:  # Aviso quando muito baixo
        st.markdown(f"""
        <div class="limit-warning">
            📊 <strong>Amostra Pequena:</strong> Analisando apenas {percentage:.1f}% dos dados ({record_limit:,} de {total_records:,}).
            Para análises mais abrangentes, considere aumentar o limite.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Função para pré-processar a consulta do usuário


def preprocess_user_query(query):
    """Melhora a consulta do usuário para melhor interpretação pela IA"""
    improvements = {
        "app": "canal = 'app' OR canal = 'mobile' OR canal = 'aplicativo'",
        "maio": "MONTH(data_compra) = 5 OR strftime('%m', data_compra) = '05'",
        "junho": "MONTH(data_compra) = 6 OR strftime('%m', data_compra) = '06'",
        "julho": "MONTH(data_compra) = 7 OR strftime('%m', data_compra) = '07'",
        "via app": "através do aplicativo móvel",
        "compraram": "fizeram compras"}

    processed_query = query
    context_hint = " (Considere que temos dados de clientes com colunas como: nome, estado, cidade, data_compra, canal_venda, valor_compra)"
    return processed_query + context_hint


def get_relevant_metric_columns(df):
    """Identifica colunas numéricas relevantes para métricas"""
    if df.empty:
        return []

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    irrelevant_patterns = ['id', 'idade', 'ano', 'mes', 'dia', '_id']
    relevant_cols = []

    for col in numeric_cols:
        col_lower = col.lower()
        if not any(pattern in col_lower for pattern in irrelevant_patterns):
            relevant_cols.append(col)
        elif any(pattern in col_lower for pattern in ['valor', 'preco', 'total', 'vendas', 'quantidade', 'count']):
            relevant_cols.append(col)

    return relevant_cols


def apply_table_sorting(df, sort_column, sort_order):
    """Aplica ordenação à tabela"""
    if sort_column == "Não ordenar" or sort_column not in df.columns:
        return df

    ascending = True if sort_order == "Crescente (menor → maior)" else False
    return df.sort_values(by=sort_column, ascending=ascending)


def apply_record_limit(sql_query, limit):
    """Aplica limite de registros à query SQL"""
    if limit and limit > 0:
        # Verifica se já tem LIMIT na query
        if "LIMIT" not in sql_query.upper():
            sql_query += f" LIMIT {limit}"
        else:
            # Substitui o LIMIT existente
            import re
            sql_query = re.sub(
                r'LIMIT\s+\d+',
                f'LIMIT {limit}',
                sql_query,
                flags=re.IGNORECASE)

    return sql_query


def generate_agent_insights(
        data,
        user_query,
        agents_manager,
        record_limit,
        total_available):
    """Gera insights elaborados pelo agente baseado nos dados"""
    if data.empty:
        return "Nenhum dado disponível para análise."

    # Preparar contexto dos dados para o agente
    data_context = {
        "total_records": len(data),
        "total_available": total_available,
        "record_limit": record_limit,
        "limited_analysis": len(data) >= record_limit and total_available > record_limit,
        "columns": list(
            data.columns),
        "numeric_columns": list(
            data.select_dtypes(
                include=['number']).columns),
        "categorical_columns": list(
            data.select_dtypes(
                include=['object']).columns),
    }

    # Calcular estatísticas básicas se houver colunas numéricas
    numeric_stats = {}
    for col in data_context["numeric_columns"]:
        numeric_stats[col] = {
            "total": float(data[col].sum()),
            "average": float(data[col].mean()),
            "max": float(data[col].max()),
            "min": float(data[col].min()),
            "std": float(data[col].std()) if len(data) > 1 else 0
        }

    # Top valores para colunas categóricas
    categorical_insights = {}
    for col in data_context["categorical_columns"]:
        if col in data.columns:
            top_values = data[col].value_counts().head(3).to_dict()
            categorical_insights[col] = {
                str(k): int(v) for k, v in top_values.items()}

    # Construir prompt para o agente gerar insights
    limitation_note = ""
    if data_context["limited_analysis"]:
        limitation_note = f"""
        IMPORTANTE: Esta análise foi limitada a {record_limit:,} registros de um total de {total_available:,} disponíveis.
        Os insights representam uma amostra dos dados completos.
        """

    insights_prompt = f"""
    Analise os dados fornecidos e gere insights elaborados e relevantes:

    Consulta do usuário: {user_query}

    {limitation_note}

    Dados analisados:
    - Registros analisados: {data_context['total_records']:,}
    - Total disponível no banco: {data_context['total_available']:,}
    - Colunas disponíveis: {', '.join(data_context['columns'])}

    Estatísticas numéricas:
    {json.dumps(numeric_stats, indent=2) if numeric_stats else 'Nenhuma coluna numérica encontrada'}

    Principais valores categóricos:
    {json.dumps(categorical_insights, indent=2) if categorical_insights else 'Nenhuma coluna categórica encontrada'}

    Gere um resumo analítico com:
    1. Principais descobertas dos dados {"(baseado na amostra)" if data_context["limited_analysis"] else ""}
    2. Tendências identificadas
    3. Insights de negócio relevantes
    4. Recomendações baseadas nos padrões encontrados

    Se a análise foi limitada, mencione isso nas conclusões.
    Seja específico com números e percentuais quando relevante.
    Use uma linguagem clara e profissional.
    Limite a resposta a 300 palavras.
    """

    try:
        # Usar o agente para gerar insights
        insights_response = agents_manager.llm(insights_prompt)
        return insights_response.strip()
    except Exception as e:
        # Fallback para insights básicos se o agente falhar
        return generate_basic_insights(
            data,
            numeric_stats,
            categorical_insights,
            data_context["limited_analysis"],
            record_limit,
            total_available)


def generate_basic_insights(
        data,
        numeric_stats,
        categorical_insights,
        is_limited,
        record_limit,
        total_available):
    """Gera insights básicos como fallback"""
    insights = []

    if is_limited:
        insights.append(
            f"Esta análise examinou {
                len(data):,    } registros (amostra de {
                total_available:,        } disponíveis) com {
                len(
                    data.columns)} variáveis.")
    else:
        insights.append(
            f"Esta análise examinou {len(data):,} registros com {len(data.columns)} variáveis.")

    if numeric_stats:
        main_numeric = list(numeric_stats.keys())[0]
        stats = numeric_stats[main_numeric]
        insights.append(
            f"A variável '{main_numeric}' apresenta um total de {
                stats['total']:,.2f} com média de {
                stats['average']:,.2f}.")

        if stats['std'] > 0:
            cv = (stats['std'] / stats['average']) * \
                100 if stats['average'] > 0 else 0
            if cv > 50:
                insights.append(
                    f"Observa-se alta variabilidade nos dados ({cv:.1f}% de coeficiente de variação).")
            else:
                insights.append(
                    f"Os dados apresentam variabilidade moderada ({
                        cv:.1f}% de coeficiente de variação).")

    if categorical_insights:
        main_categorical = list(categorical_insights.keys())[0]
        top_category = list(categorical_insights[main_categorical].items())[0]
        total_cat = sum(categorical_insights[main_categorical].values())
        percentage = (top_category[1] / total_cat) * 100
        insights.append(
            f"Em '{main_categorical}', '{
                top_category[0]}' representa {
                percentage:.1f}% dos casos ({
                top_category[1]:,            } registros).")

    if is_limited:
        insights.append(
            "Os resultados são baseados na amostra analisada e podem variar ao considerar todos os dados.")
    else:
        insights.append(
            "Estes dados fornecem uma base sólida para tomada de decisões estratégicas.")

    return " ".join(insights)


def format_analysis_summary(agent_insights, data):
    """Formata o resumo da análise com insights do agente"""
    formatted_summary = f"""
    <div class="summary-container">
        <div class="summary-header">
            <div class="summary-icon">🔍</div>
            <div class="summary-title">Resumo da Análise</div>
        </div>
        <div class="summary-content">
            {agent_insights}
        </div>
    </div>
    """

    return formatted_summary


# Botão de análise
if st.button("🚀 Analisar Dados", type="primary", disabled=not api_configured):
    if not user_input.strip():
        st.warning("⚠️ Por favor, descreva sua análise!")
        st.stop()

    # Inicializar LLM e Agents
    try:
        if "llm" not in st.session_state or "agents" not in st.session_state:
            with st.spinner("🔧 Inicializando IA..."):
                st.session_state.llm = OpenAI(
                    openai_api_key=openai_key,
                    temperature=0.3,
                    max_tokens=2000,
                    model="gpt-3.5-turbo-instruct"
                )
                st.session_state.agents = AgentsManager(
                    st.session_state.llm,
                    st.session_state.db
                )
    except Exception as e:
        st.error(f"❌ Erro ao inicializar IA: {e}")
        st.stop()

    # Processamento da análise
    with st.spinner("🔄 Processando sua solicitação..."):
        try:
            processed_input = preprocess_user_query(user_input)
            interpretation = st.session_state.agents.interpret_request(
                processed_input)

            # Determinar o tipo de saída com base no prompt do usuário
            if "tabela" in user_input.lower() or "lista" in user_input.lower():
                output_type = "📋 Tabela"
            elif "gráfico" in user_input.lower() or "grafico" in user_input.lower() or "chart" in user_input.lower() or "visualização" in user_input.lower() or "visualizacao" in user_input.lower():
                output_type = "📊 Gráfico"
            elif "resumo" in user_input.lower() or "texto" in user_input.lower():
                output_type = "📝 Texto"
            else:
                output_type = "📋 Tabela"  # Padrão para tabela se não for especificado

            # Mapear a seleção do usuário para o tipo de gráfico
            chart_type_mapping = {
                "Barras": "barras",
                "Linhas": "linhas",
                "Pizza": "pizza",
                "Área": "area",
                "Dispersão": "dispersao"
            }

            interpretation["tipo_grafico"] = chart_type_mapping.get(
                chart_type, "barras")

            sql_query = st.session_state.agents.generate_sql(interpretation)

            # Obter total de registros disponíveis antes de aplicar o limite
            count_query = f"SELECT COUNT(*) as total FROM ({
                sql_query.split('LIMIT')[0].strip()}) as subquery"
            try:
                count_result = st.session_state.db.execute_query(count_query)
                total_available = count_result.iloc[0]['total'] if count_result is not None and len(
                    count_result) > 0 else 0
            except BaseException:
                # Fallback: executar query original sem LIMIT e contar
                try:
                    temp_query = sql_query.split('LIMIT')[0].strip()
                    temp_result = st.session_state.db.execute_query(temp_query)
                    total_available = len(
                        temp_result) if temp_result is not None else 0
                except BaseException:
                    total_available = 0

            # Aplicar limite de registros à query
            limited_sql_query = apply_record_limit(sql_query, record_limit)
            results = st.session_state.db.execute_query(limited_sql_query)

            if results is None or (
                isinstance(
                    results,
                    pd.DataFrame) and len(results) == 0):
                st.warning(
                    "⚠️ A consulta não retornou dados. Verificando possíveis problemas...")
                st.code(limited_sql_query, language="sql")

                try:
                    test_query = "SELECT COUNT(*) as total FROM clientes LIMIT 1"
                    test_result = st.session_state.db.execute_query(test_query)
                    if test_result is not None and len(test_result) > 0:
                        st.info(
                            f"Total de registros na tabela clientes: {
                                test_result.iloc[0]['total']}")

                    schema_query = "PRAGMA table_info(clientes)"
                    schema_result = st.session_state.db.execute_query(
                        schema_query)
                    if schema_result is not None and len(schema_result) > 0:
                        st.write("Estrutura da tabela:")
                        st.dataframe(schema_result)

                    sample_query = "SELECT * FROM clientes LIMIT 5"
                    sample_result = st.session_state.db.execute_query(
                        sample_query)
                    if sample_result is not None and len(sample_result) > 0:
                        st.write("Dados de exemplo:")
                        st.dataframe(sample_result)
                except Exception as debug_e:
                    st.error(f"Erro no diagnóstico: {debug_e}")

                st.stop()

            # Gerar insights elaborados pelo agente
            with st.spinner("🧠 Gerando insights inteligentes..."):
                agent_insights = generate_agent_insights(
                    results, user_input, st.session_state.agents, record_limit, total_available)

            response = st.session_state.agents.format_complete_response(
                results, interpretation, user_input
            )

            # Substituir o summary original pelos insights do agente
            response["summary"] = agent_insights
            response["total_available"] = total_available
            response["record_limit"] = record_limit
            response["is_limited"] = len(
                results) >= record_limit and total_available > record_limit

            st.session_state.last_response = response
            st.session_state.last_query = limited_sql_query
            st.session_state.interpretation = interpretation
            st.session_state.output_type = output_type

        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            st.subheader("🔍 Detalhes do Erro:")

            with st.expander("Informações Técnicas", expanded=True):
                st.write("**Erro:**", str(e))

                if 'interpretation' in locals():
                    st.write("**Interpretação gerada:**")
                    st.json(interpretation)

                if 'limited_sql_query' in locals():
                    st.write("**Query SQL gerada:**")
                    st.code(limited_sql_query, language="sql")

                    st.write("**💡 Possíveis correções:**")
                    st.markdown("""
                    - Verifique se os nomes das colunas existem na tabela
                    - Confirme o formato das datas (YYYY-MM-DD)
                    - Teste filtros mais simples primeiro
                    - Verifique se a tabela tem os dados esperados
                    """)

                try:
                    st.write("**📊 Schema do Banco:**")
                    schema = st.session_state.db.get_database_schema()
                    st.json(schema)
                except BaseException:
                    st.write("Não foi possível carregar o schema do banco")

            st.stop()

# Exibição dos resultados
if 'last_response' in st.session_state:
    response = st.session_state.last_response
    output_type = st.session_state.get('output_type', '📋 Tabela')

    if not response["success"]:
        st.markdown(f"""
        <div class="error-box">
            <strong>❌ Erro na análise:</strong><br>
            {response["summary"]}
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Container principal de resultados
    with st.container():
        st.markdown('<div class="output-container">', unsafe_allow_html=True)

        st.markdown(
            f'<h2 class="result-title">🔍 Resultados da Análise</h2>',
            unsafe_allow_html=True)
        st.markdown(
            f'<p class="result-subtitle">📌 {
                response["interpretation"]["intencao"]} | Tipo: {output_type}</p>',
            unsafe_allow_html=True)

        # Aviso sobre limitação se aplicável
        if response.get("is_limited", False):
            st.markdown(f"""
            <div class="limit-warning">
                📊 <strong>Análise Limitada:</strong> Exibindo {len(response['data']):,} de {response.get('total_available', 0):,} registros disponíveis.
                Para ver todos os dados, aumente o limite de registros.
            </div>
            """, unsafe_allow_html=True)

        # Resumo formatado com insights do agente
        formatted_summary = format_analysis_summary(
            response["summary"], response["data"])
        st.markdown(formatted_summary, unsafe_allow_html=True)

        # Info com detalhes dos registros
        total_available = response.get(
            'total_available', len(
                response['data']))
        if response.get("is_limited", False):
            st.info(
                f"📊 **{
                    len(
                        response['data']):,                           }** registros analisados de **{
                    total_available:,                                                                                                            }** disponíveis | **{
                    len(
                        response['data'].columns)}** colunas")
        else:
            st.info(
                f"📊 **{len(response['data'])}** registros encontrados | **{len(response['data'].columns)}** colunas")

        if len(
            response["data"]) > 0 and len(
            response["data"].select_dtypes(
                include=['number']).columns) > 0:
            metric_cols = st.columns(3)

            with metric_cols[0]:
                if response.get("is_limited", False):
                    st.metric(
                        "📋 Registros Analisados", f"{
                            len(
                                response['data']):,                                 }", delta=f"de {
                            total_available:,                                          } total")
                else:
                    st.metric(
                        "📋 Total de Registros", f"{
                            response['total_records']:,}", delta=None)

            relevant_cols = get_relevant_metric_columns(response["data"])

            if len(relevant_cols) >= 1:
                with metric_cols[1]:
                    col_name = relevant_cols[0]
                    total_value = response["data"][col_name].sum()
                    display_name = col_name.replace('_', ' ').title()

                    if 'valor' in col_name.lower() or 'preco' in col_name.lower():
                        label = f"💰 Total {display_name}"
                        if response.get("is_limited", False):
                            label += " (amostra)"
                        st.metric(label, f"R$ {total_value:,.2f}", delta=None)
                    else:
                        label = f"📊 Total {display_name}"
                        if response.get("is_limited", False):
                            label += " (amostra)"
                        st.metric(label, f"{total_value:,.0f}", delta=None)

            if len(relevant_cols) >= 1:
                with metric_cols[2]:
                    col_name = relevant_cols[0]
                    avg_value = response["data"][col_name].mean()
                    display_name = col_name.replace('_', ' ').title()

                    if 'valor' in col_name.lower() or 'preco' in col_name.lower():
                        st.metric(
                            f"📊 Média {display_name}", f"R$ {
                                avg_value:,.2f}", delta=None)
                    else:
                        st.metric(
                            f"📊 Média {display_name}", f"{
                                avg_value:,.2f}", delta=None)

        if len(response["data"]) == 0:
            st.warning("⚠️ Nenhum resultado encontrado para sua consulta.")
            st.markdown("""
            **Possíveis motivos:**
            - Os critérios de filtro são muito restritivos
            - Os dados solicitados não existem no banco
            - Problema na formatação da data ou outros campos
            """)

            with st.expander("🔍 Detalhes da Consulta", expanded=True):
                st.subheader("Query SQL Executada:")
                st.code(st.session_state.last_query, language="sql")

                st.subheader("Interpretação da IA:")
                st.json(st.session_state.interpretation)

                st.subheader("💡 Sugestões:")
                st.markdown("""
                1. Verifique se os nomes das colunas estão corretos
                2. Confirme se os dados existem no período solicitado
                3. Teste uma consulta mais simples primeiro
                4. Verifique o formato das datas no banco
                """)

            st.stop()

        # Exibir resultados com base no tipo de saída determinado
        if output_type == "📋 Tabela":
            st.subheader("📋 Dados Tabulares")

            st.markdown('<div class="sort-controls">', unsafe_allow_html=True)
            st.markdown("**🔄 Opções de Ordenação**")

            col_sort1, col_sort2, col_sort3 = st.columns([3, 2, 2])

            with col_sort1:
                sort_options = ["Não ordenar"] + list(response["data"].columns)
                sort_column = st.selectbox(
                    "📊 Ordenar por coluna:",
                    options=sort_options,
                    key="sort_column_select"
                )

            with col_sort2:
                sort_order = st.selectbox(
                    "🔄 Ordem:",
                    options=[
                        "Crescente (menor → maior)",
                        "Decrescente (maior → menor)"],
                    key="sort_order_select")

            with col_sort3:
                display_limit = st.selectbox(
                    "📄 Mostrar registros:",
                    options=[50, 100, 200, 500, "Todos"],
                    index=1,
                    key="display_limit_select"
                )

            st.markdown('</div>', unsafe_allow_html=True)

            display_df = response["data"].copy()

            if sort_column != "Não ordenar":
                display_df = apply_table_sorting(
                    display_df, sort_column, sort_order)

            if display_limit != "Todos":
                display_df = display_df.head(display_limit)

            if sort_column != "Não ordenar":
                order_text = "crescente" if "Crescente" in sort_order else "decrescente"
                info_text = f"📊 Tabela ordenada por **{sort_column}** em ordem **{order_text}** | Exibindo **{
                    len(display_df):,                }** de **{
                    len(
                        response['data']):,                    }** registros"
                if response.get("is_limited", False):
                    info_text += f" (de {total_available:,} total no banco)"
                st.info(info_text)
            else:
                info_text = f"📊 Exibindo **{
                    len(display_df):,                                            }** de **{
                    len(
                        response['data']):,                                                                                                                   }** registros"
                if response.get("is_limited", False):
                    info_text += f" (de {total_available:,} total no banco)"
                st.info(info_text)

            # Correção para exibir a tabela corretamente
            st.markdown(
                '<div class="table-container">',
                unsafe_allow_html=True)
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(500, 35 * len(display_df))
            )
            st.markdown('</div>', unsafe_allow_html=True)

            col_download1, col_download2 = st.columns(2)

            with col_download1:
                csv_displayed = display_df.to_csv(
                    index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Exportar Dados Exibidos",
                    csv_displayed,
                    file_name=f"analise_exibida_{
                        datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Baixe apenas os dados exibidos na tabela (com ordenação aplicada)")

            with col_download2:
                csv_all = response["data"].to_csv(
                    index=False, encoding='utf-8-sig')
                download_text = "📥 Exportar Dados Analisados"
                help_text = "Baixe todos os dados da consulta atual"
                if response.get("is_limited", False):
                    download_text += f" ({len(response['data']):,} reg.)"
                    help_text += f" (limitado a {len(response['data']):,} registros)"

                st.download_button(
                    download_text,
                    csv_all,
                    file_name=f"analise_completa_{
                        datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help=help_text)

        elif output_type == "📊 Gráfico":
            st.subheader("📊 Visualização Gráfica")

            if len(
                    response["data"].columns) >= 2 and len(
                    response["data"]) > 0:
                try:
                    x_col = response["data"].columns[0]
                    y_col = response["data"].columns[1]

                    # Título do gráfico
                    title_suffix = ""
                    if response.get("is_limited", False):
                        title_suffix = f" (amostra de {
                            len(
                                response['data']):,                            } registros)"

                    # Informação sobre o tipo de gráfico selecionado
                    st.info(
                        f"📊 Gerando **{chart_type}** com dados: **{x_col}** vs **{y_col}**")

                    # Gera o gráfico com base na seleção do usuário
                    if chart_type == "Barras":
                        fig = px.bar(
                            response["data"],
                            x=x_col,
                            y=y_col,
                            title=f"Gráfico de Barras: {y_col} por {x_col}{title_suffix}")
                    elif chart_type == "Linhas":
                        fig = px.line(
                            response["data"],
                            x=x_col,
                            y=y_col,
                            title=f"Gráfico de Linhas: {y_col} por {x_col}{title_suffix}")
                    elif chart_type == "Pizza":
                        fig = px.pie(
                            response["data"],
                            values=y_col,
                            names=x_col,
                            title=f"Gráfico de Pizza: Distribuição de {y_col}{title_suffix}")
                    elif chart_type == "Área":
                        fig = px.area(
                            response["data"],
                            x=x_col,
                            y=y_col,
                            title=f"Gráfico de Área: {y_col} por {x_col}{title_suffix}")
                    elif chart_type == "Dispersão":
                        fig = px.scatter(
                            response["data"],
                            x=x_col,
                            y=y_col,
                            title=f"Gráfico de Dispersão: {y_col} vs {x_col}{title_suffix}")
                    else:
                        fig = px.bar(
                            response["data"], x=x_col, y=y_col)  # Default

                    # Aplicar tema escuro ao gráfico
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#f8fafc',
                        title_font_color='#f8fafc'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Mostrar também os dados em tabela para referência
                    with st.expander("📋 Ver dados utilizados no gráfico"):
                        st.dataframe(
                            response["data"], use_container_width=True)

                except Exception as e:
                    st.warning(
                        f"⚠️ Erro ao gerar gráfico interativo: {
                            str(e)}")
                    st.info("📋 Exibindo dados em formato tabular")
                    st.dataframe(response["data"])
            else:
                st.warning(
                    "⚠️ Dados insuficientes para gerar gráfico. É necessário pelo menos 2 colunas.")
                st.info(
                    "💡 **Dica:** Certifique-se de que sua consulta retorne dados com pelo menos duas colunas (uma para X e uma para Y)")
                st.dataframe(response["data"])

        elif output_type == "📝 Texto":
            st.subheader("📝 Resumo Textual")

            # Exibir o resumo em formato mais elaborado
            st.markdown(f"""
            <div class="insight-box">
                {response["summary"]}
            </div>
            """, unsafe_allow_html=True)

            # Adicionar estatísticas básicas se disponíveis
            if len(response["data"]) > 0:
                st.subheader("📈 Estatísticas Complementares")

                # Estatísticas para colunas numéricas
                numeric_cols = response["data"].select_dtypes(
                    include=['number']).columns
                if len(numeric_cols) > 0:
                    st.write("**Colunas Numéricas:**")
                    stats_df = response["data"][numeric_cols].describe()
                    st.dataframe(stats_df, use_container_width=True)

                # Top valores para colunas categóricas
                categorical_cols = response["data"].select_dtypes(
                    include=['object']).columns
                if len(categorical_cols) > 0:
                    st.write("**Principais Valores por Categoria:**")
                    for col in categorical_cols[:3]:  # Limitar a 3 colunas
                        top_values = response["data"][col].value_counts().head(
                            5)
                        st.write(f"*{col}:*")
                        for value, count in top_values.items():
                            percentage = (count / len(response["data"])) * 100
                            st.write(
                                f"  - {value}: {count:,} ({percentage:.1f}%)")

        st.markdown('</div>', unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div class="footer">
    <p>📅 Última atualização: {datetime} | 📊 {records} registros no banco</p>
    <p>Desenvolvido por <a href="https://github.com/Filip3Owl" target="_blank">Filipe Rangel</a></p>
</div>
""".format(
    datetime=datetime.now().strftime('%d/%m/%Y %H:%M'),
    records=total_records
), unsafe_allow_html=True)
