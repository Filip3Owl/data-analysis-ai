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
plt.rcParams['text.color'] = '#1e293b'
plt.rcParams['axes.labelcolor'] = '#1e293b'
plt.rcParams['xtick.color'] = '#1e293b'
plt.rcParams['ytick.color'] = '#1e293b'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'

# CSS customizado melhorado com botões de exemplo
st.markdown("""
<style>
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --light-bg: #f8fafc;
        --dark-text: #1e293b;      /* Texto escuro para melhor legibilidade */
        --light-text: #f8fafc;
        --card-bg: #ffffff;        /* Fundo branco para cards */
        --container-bg: #f8fafc;   /* Fundo claro para containers */
        --sidebar-bg: #ffffff;     /* Fundo branco para sidebar */
        --schema-bg: #f1f5f9;      /* Fundo cinza claro para schema */
        --border-color: #e2e8f0;
        --success-color: #10b981;
        --warning-color: #f59e0b;
    }

    body {
        background-color: var(--light-bg);
    }

    .main-header {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: var(--light-text);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .author-credit {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .author-credit strong {
        font-size: 1.1em;
    }

    .input-container {
        background-color: var(--container-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
        color: var(--dark-text);
    }

    .output-container {
        background-color: var(--container-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
        color: var(--dark-text);
    }

    .summary-container {
        background-color: var(--card-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        margin-bottom: 1rem;
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: var(--dark-text);
    }

    .insight-box {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #2c3e50;
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
        color: var(--dark-text);
    }

    .dataframe {
        width: 100% !important;
        color: var(--dark-text) !important;
    }

    .dataframe th {
        background-color: var(--primary) !important;
        color: white !important;
        position: sticky;
        top: 0;
        font-weight: 600;
    }

    .dataframe td {
        color: var(--dark-text) !important;
        background-color: var(--card-bg) !important;
    }

    .stButton>button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        margin-top: 1rem;
        transition: all 0.2s;
        font-weight: 500;
    }

    .error-box {
        background-color: #fee2e2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        margin: 1rem 0;
        color: #b91c1c;
    }

    .result-title {
        color: var(--dark-text);
        margin-bottom: 0.5rem;
    }

    .result-subtitle {
        color: var(--dark-text);
        opacity: 0.8;
        margin-bottom: 1rem;
    }

    /* Melhorias para gráficos */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly div {
        color: var(--dark-text) !important;
    }

    /* Ajuste para o expander */
    .st-expander {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background-color: var(--card-bg);
    }

    .st-expander .st-expanderHeader {
        color: var(--dark-text) !important;
        font-weight: 600;
        background-color: var(--card-bg) !important;
    }

    .st-expander .st-expanderContent {
        color: var(--dark-text) !important;
        background-color: var(--card-bg) !important;
    }

    /* Correção para informações do schema - PROBLEMA PRINCIPAL */
    .schema-info {
        background: var(--schema-bg) !important;
        padding: 0.8rem !important;
        border-radius: 6px !important;
        margin: 0.4rem 0 !important;
        font-size: 0.9rem !important;
        color: var(--dark-text) !important;
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

    /* Botões da sidebar - MELHORADO PARA EXEMPLOS */
    .stButton button {
        width: 100% !important;
        text-align: left !important;
        background-color: var(--card-bg) !important;
        color: var(--dark-text) !important;
        border: 1px solid var(--border-color) !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton button:hover {
        background-color: var(--primary) !important;
        color: white !important;
        border-color: var(--primary) !important;
        transform: translateX(2px) !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3) !important;
    }

    .stButton button:active {
        background-color: var(--success-color) !important;
        border-color: var(--success-color) !important;
        transform: translateX(0px) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4) !important;
    }

    /* Indicador visual para botão clicado */
    .stButton button:focus {
        background-color: var(--success-color) !important;
        border-color: var(--success-color) !important;
        color: white !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3) !important;
    }

    /* Animação de pulso para indicar clique */
    @keyframes button-pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .stButton button.clicked {
        animation: button-pulse 0.6s !important;
        background-color: var(--success-color) !important;
        border-color: var(--success-color) !important;
        color: white !important;
    }

    /* Texto da sidebar */
    .css-1d391kg .stMarkdown {
        color: var(--dark-text) !important;
    }

    /* Subheaders da sidebar */
    .css-1d391kg h2, .css-1d391kg h3 {
        color: var(--dark-text) !important;
    }

    /* Footer styling */
    .footer {
        background-color: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        border-top: 2px solid var(--primary);
        margin-top: 2rem;
        text-align: center;
        color: var(--dark-text);
        font-size: 0.9rem;
    }

    .footer a {
        color: var(--primary);
        text-decoration: none;
        font-weight: 500;
    }

    .footer a:hover {
        text-decoration: underline;
    }

    /* Estilo para botão selecionado */
    .selected-example-button {
        background-color: var(--success-color) !important;
        border-color: var(--success-color) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Indicador de status da query */
    .query-status {
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .query-status.success {
        background-color: #d1fae5;
        color: #065f46;
        border-left: 4px solid var(--success-color);
    }

    .query-status.error {
        background-color: #fee2e2;
        color: #991b1b;
        border-left: 4px solid #dc2626;
    }

    .query-status.warning {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 4px solid var(--warning-color);
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

# Créditos do autor
st.markdown("""
<div class="author-credit">
    <strong>🚀 Desenvolvido por Filipe Rangel</strong><br>
    Aplicação de Analytics com Inteligência Artificial para análise de dados
</div>
""", unsafe_allow_html=True)

# Verificação do banco de dados
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'

@st.cache_data
def quick_database_check():
    if not DB_PATH.exists():
        return False, f"Arquivo não encontrado: {DB_PATH}"

    if DB_PATH.stat().st_size == 0:
        return False, "Arquivo do banco está vazio"

    try:
        with DatabaseManager(str(DB_PATH)) as db:
            health = db.health_check()
            if not health["connected"]:
                return False, "Falha na conexão"
            if health["total_records"] == 0:
                return False, "Banco sem dados"
            return True, f"✅ {health['tables_count']} tabelas, {health['total_records']:,} registros"
    except Exception as e:
        return False, f"Erro: {str(e)}"

db_ok, db_message = quick_database_check()

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

# Funções auxiliares para diagnóstico
def execute_query_with_debug(db, query):
    """Executa query com informações de debug detalhadas"""
    import time
    
    start_time = time.time()
    result = {
        'query': query,
        'success': False,
        'error': None,
        'execution_time': 0,
        'row_count': 0,
        'similar_queries': []
    }
    
    try:
        data = db.execute_query(query)
        result['execution_time'] = time.time() - start_time
        
        if data is not None and len(data) > 0:
            result['success'] = True
            result['row_count'] = len(data)
        else:
            result['success'] = True
            result['row_count'] = 0
            
        # Gerar queries similares sugeridas
        result['similar_queries'] = generate_similar_queries(db, query)
        
    except Exception as e:
        result['error'] = str(e)
        result['execution_time'] = time.time() - start_time
        result['similar_queries'] = generate_fallback_queries(db)
    
    return result

def generate_similar_queries(db, original_query):
    """Gera queries similares baseadas na original"""
    suggestions = []
    
    # Queries básicas de exploração
    tables = db.get_all_tables()
    
    for table in tables:
        suggestions.extend([
            f"SELECT * FROM {table} LIMIT 10",
            f"SELECT COUNT(*) as total FROM {table}",
            f"SELECT * FROM {table} WHERE rowid IN (1,2,3,4,5)"
        ])
    
    # Se a query original menciona 'app' ou 'maio'
    if 'app' in original_query.lower():
        for table in tables:
            columns = db.get_table_columns(table)
            canal_cols = [col for col in columns if 'canal' in col.lower()]
            for col in canal_cols:
                suggestions.append(f"SELECT DISTINCT {col} FROM {table}")
                suggestions.append(f"SELECT {col}, COUNT(*) FROM {table} GROUP BY {col}")
    
    if 'maio' in original_query.lower() or '05' in original_query:
        for table in tables:
            columns = db.get_table_columns(table)
            date_cols = [col for col in columns if any(term in col.lower() for term in ['data', 'date'])]
            for col in date_cols:
                suggestions.append(f"SELECT DISTINCT {col} FROM {table} LIMIT 10")
    
    return suggestions[:5]  # Limitar a 5 sugestões

def generate_fallback_queries(db):
    """Gera queries básicas de fallback quando há erro"""
    queries = []
    tables = db.get_all_tables()
    
    for table in tables[:3]:  # Limitar a 3 tabelas
        queries.extend([
            f"SELECT * FROM {table} LIMIT 5",
            f"SELECT COUNT(*) as registros FROM {table}"
        ])
    
    return queries

def diagnose_query_failure(db, query):
    """Diagnostica por que uma query falhou"""
    diagnosis = {
        'issues_found': [],
        'suggestions': [],
        'table_info': {},
        'sample_data': {}
    }
    
    try:
        # Analisar tabelas mencionadas na query
        tables = db.get_all_tables()
        
        for table in tables:
            try:
                columns = db.get_table_columns(table)
                types = db.get_column_types(table) if hasattr(db, 'get_column_types') else ['TEXT'] * len(columns)
                count = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                
                diagnosis['table_info'][table] = {
                    'columns': columns,
                    'types': types,
                    'count': count.iloc[0]['count'] if count is not None and len(count) > 0 else 0
                }
                
                # Amostra de dados
                sample = db.execute_query(f"SELECT * FROM {table} LIMIT 3")
                if sample is not None and len(sample) > 0:
                    diagnosis['sample_data'][table] = sample.to_dict('records')
                    
            except Exception as e:
                diagnosis['issues_found'].append(f"Erro ao analisar tabela {table}: {str(e)}")
        
        # Verificações específicas
        if 'app' in query.lower():
            diagnosis['suggestions'].append("Verifique se existe uma coluna 'canal', 'canal_venda' ou similar")
            diagnosis['suggestions'].append("Teste diferentes valores: 'app', 'mobile', 'aplicativo'")
        
        if 'maio' in query.lower():
            diagnosis['suggestions'].append("Verifique o formato das datas no banco")
            diagnosis['suggestions'].append("Teste com diferentes formatos: '2024-05', 'maio', '05'")
        
        if 'estado' in query.lower():
            diagnosis['suggestions'].append("Verifique se existe coluna 'estado', 'uf' ou 'regiao'")
    
    except Exception as e:
        diagnosis['issues_found'].append(f"Erro no diagnóstico: {str(e)}")
    
    return diagnosis

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
                                • <strong>{col}</strong> <span style='color: #666;'>({col_type})</span>
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

    st.divider()

    # Inicializar estado para botão selecionado
    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None

    # Exemplos de consultas - EXPANDIDOS
    st.subheader("💡 Exemplos de Consultas")
    exemplos = {
        # Análises de Clientes
        "Distribuição de clientes por faixa etária": "📊 Gráfico",
        "Clientes por estado e gênero": "📊 Gráfico",
        "Top 10 cidades com mais clientes": "📋 Tabela",
        "Profissões mais comuns dos clientes": "📊 Gráfico",
        
        # Análises de Compras
        "Vendas totais por mês em 2024": "📊 Gráfico",
        "Top 5 categorias mais vendidas": "📋 Tabela",
        "Ticket médio por canal de venda": "📋 Tabela",
        "Vendas por dia da semana": "📊 Gráfico",
        
        # Análises de Suporte
        "Chamados não resolvidos por tipo": "📊 Gráfico",
        "Tempo médio para resolução por canal": "📋 Tabela",
        "Eficiência na resolução por mês": "📊 Gráfico",
        
        # Análises de Campanhas
        "Taxa de interação por campanha": "📊 Gráfico",
        "Conversão de campanhas por canal": "📋 Tabela",
        "Clientes que interagiram mas não compraram": "📋 Tabela",
        
        # Análises Cruzadas
        "Relação entre idade e valor médio de compra": "📊 Gráfico",
        "Clientes que compram mais por categoria": "📋 Tabela",
        "Eficácia de campanhas por região": "📊 Gráfico"
    }

    # Organizar exemplos em categorias
    st.markdown("**👥 Análises de Clientes:**")
    clientes_exemplos = {k: v for k, v in exemplos.items() if "cliente" in k.lower() or "idade" in k.lower() or "gênero" in k.lower() or "cidade" in k.lower() or "profiss" in k.lower()}
    
    for exemplo, tipo in clientes_exemplos.items():
        is_selected = st.session_state.selected_example == exemplo
        button_key = f"exemplo_clientes_{exemplo}"
        if st.button(f"{tipo} {exemplo}", key=button_key):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo
            st.session_state.selected_example = exemplo
            st.rerun()

    st.markdown("**🛒 Análises de Compras:**")
    compras_exemplos = {k: v for k, v in exemplos.items() if "venda" in k.lower() or "compra" in k.lower() or "ticket" in k.lower() or "categoria" in k.lower()}
    
    for exemplo, tipo in compras_exemplos.items():
        is_selected = st.session_state.selected_example == exemplo
        button_key = f"exemplo_compras_{exemplo}"
        if st.button(f"{tipo} {exemplo}", key=button_key):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo
            st.session_state.selected_example = exemplo
            st.rerun()

    st.markdown("**🆘 Análises de Suporte:**")
    suporte_exemplos = {k: v for k, v in exemplos.items() if "suporte" in k.lower() or "chamado" in k.lower() or "resolu" in k.lower()}
    
    for exemplo, tipo in suporte_exemplos.items():
        is_selected = st.session_state.selected_example == exemplo
        button_key = f"exemplo_suporte_{exemplo}"
        if st.button(f"{tipo} {exemplo}", key=button_key):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo
            st.session_state.selected_example = exemplo
            st.rerun()

    st.markdown("**📢 Análises de Campanhas:**")
    campanhas_exemplos = {k: v for k, v in exemplos.items() if "campanha" in k.lower() or "intera" in k.lower() or "convers" in k.lower()}
    
    for exemplo, tipo in campanhas_exemplos.items():
        is_selected = st.session_state.selected_example == exemplo
        button_key = f"exemplo_campanhas_{exemplo}"
        if st.button(f"{tipo} {exemplo}", key=button_key):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo
            st.session_state.selected_example = exemplo
            st.rerun()

    st.markdown("**🔗 Análises Cruzadas:**")
    cruzadas_exemplos = {k: v for k, v in exemplos.items() if "rela" in k.lower() or "efici" in k.lower() or "cruzada" in k.lower()}
    
    for exemplo, tipo in cruzadas_exemplos.items():
        is_selected = st.session_state.selected_example == exemplo
        button_key = f"exemplo_cruzadas_{exemplo}"
        if st.button(f"{tipo} {exemplo}", key=button_key):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo
            st.session_state.selected_example = exemplo
            st.rerun()

# Container para área de entrada
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)

    # Campo de entrada com exemplo selecionado
    pergunta_default = st.session_state.get('exemplo_selecionado', '')

    st.markdown('<h3 class="result-title">Descreva o que você quer analisar:</h3>',
                unsafe_allow_html=True)

    user_input = st.text_area(
        " ",
        value=pergunta_default,
        height=100,
        placeholder="Ex: Mostre os 10 clientes que mais compraram em formato de tabela",
        help="Descreva sua análise em linguagem natural. Ex: 'Top 5 estados com mais vendas'",
        label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

# Opções avançadas
with st.expander("⚙️ Opções Avançadas"):
    col1, col2 = st.columns(2)

    with col1:
        show_debug = st.checkbox("🔍 Mostrar detalhes técnicos", value=False)
        auto_chart = st.checkbox("📊 Gerar gráfico automaticamente", value=True)

    with col2:
        chart_type = st.selectbox(
            "📈 Tipo de gráfico preferido",
            ["Automático", "Barras", "Pizza", "Linha", "Scatter", "Apenas Tabela"]
        )

# Função para pré-processar a consulta do usuário
def preprocess_user_query(query):
    """Melhora a consulta do usuário para melhor interpretação pela IA"""

    # Mapeamento de termos comuns
    improvements = {
        "app": "canal = 'app' OR canal = 'mobile' OR canal = 'aplicativo'",
        "maio": "MONTH(data_compra) = 5 OR strftime('%m', data_compra) = '05'",
        "junho": "MONTH(data_compra) = 6 OR strftime('%m', data_compra) = '06'",
        "julho": "MONTH(data_compra) = 7 OR strftime('%m', data_compra) = '07'",
        "via app": "através do aplicativo móvel",
        "compraram": "fizeram compras"
    }

    processed_query = query

    # Adicionar contexto sobre estrutura de dados
    context_hint = " (Considere que temos dados de clientes com colunas como: nome, estado, cidade, data_compra, canal_venda, valor_compra)"

    return processed_query + context_hint

def get_relevant_metric_columns(df):
    """Identifica colunas numéricas relevantes para métricas, excluindo IDs e outros campos irrelevantes."""
    if df.empty:
        return []

    # Colunas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    # Filtrar colunas irrelevantes
    irrelevant_patterns = ['id', 'idade', 'ano', 'mes', 'dia', '_id']
    relevant_cols = []

    for col in numeric_cols:
        col_lower = col.lower()
        # Verificar se não contém padrões irrelevantes
        if not any(pattern in col_lower for pattern in irrelevant_patterns):
            relevant_cols.append(col)
        # Incluir se contém padrões relevantes (valores monetários, quantidades)
        elif any(pattern in col_lower for pattern in ['valor', 'preco', 'total', 'vendas', 'quantidade', 'count']):
            relevant_cols.append(col)

    return relevant_cols

def apply_table_sorting(df, sort_column, sort_order):
    """Aplica ordenação à tabela"""
    if sort_column == "Não ordenar" or sort_column not in df.columns:
        return df

    ascending = True if sort_order == "Crescente (menor → maior)" else False
    return df.sort_values(by=sort_column, ascending=ascending)

# Botão de análise
if st.button("🚀 Analisar Dados", type="primary", disabled=not api_configured):
    if not user_input.strip():
        st.warning("⚠️ Por favor, descreva sua análise!")
        st.stop()

    # Limpar exemplo selecionado após análise
    if 'exemplo_selecionado' in st.session_state:
        st.session_state.selected_example = None

    # Inicializar LLM e Agents
    try:
        if "llm" not in st.session_state or "agents" not in st.session_state:
            with st.spinner("🔧 Inicializando IA..."):
                st.session_state.llm = OpenAI(
                    openai_api_key=openai_key,
                    temperature=0.3,
                    max_tokens=10000,
                    model="o4-mini-2025-04-16"
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
            # Pré-processar a consulta do usuário
            processed_input = preprocess_user_query(user_input)

            # Interpretação da solicitação
            interpretation = st.session_state.agents.interpret_request(processed_input)

            # Determinar o tipo de saída baseado no estado da sessão ou na interpretação automática
            output_type = st.session_state.get('output_type', '🔍 Automático')
            
            if output_type != "🔍 Automático":
                interpretation["tipo_grafico"] = {
                    "📋 Tabela": "tabela",
                    "📊 Gráfico": chart_type.lower(),
                    "📝 Texto": "texto"
                }.get(output_type, "tabela")

            # Geração SQL
            sql_query = st.session_state.agents.generate_sql(interpretation)

            # Executação da query
            results = st.session_state.db.execute_query(sql_query)

            # Debug avançado: mostrar resultados brutos se não há dados
            if results is None or (isinstance(results, pd.DataFrame) and len(results) == 0):
                st.warning("⚠️ A consulta não retornou dados. Executando diagnóstico avançado...")

                # Usar as funções de debug corrigidas
                debug_result = execute_query_with_debug(st.session_state.db, sql_query)
                
                with st.expander("🔍 Diagnóstico Detalhado da Query", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📊 Informações da Execução")
                        status_class = "success" if debug_result['success'] else "error"
                        st.markdown(f"""
                        <div class="query-status {status_class}">
                            <strong>Status:</strong> {'✅ Sucesso' if debug_result['success'] else '❌ Falha'}<br>
                            <strong>Tempo:</strong> {debug_result['execution_time']:.3f}s<br>
                            <strong>Registros:</strong> {debug_result['row_count']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if debug_result['error']:
                            st.error(f"**Erro:** {debug_result['error']}")
                    
                    with col2:
                        st.subheader("🔧 Query Executada")
                        st.code(debug_result['query'], language="sql")
                
                # Diagnóstico da falha
                diagnosis = diagnose_query_failure(st.session_state.db, sql_query)
                
                if diagnosis['issues_found']:
                    st.subheader("⚠️ Problemas Identificados")
                    for issue in diagnosis['issues_found']:
                        st.error(f"• {issue}")
                
                if diagnosis['suggestions']:
                    st.subheader("💡 Sugestões de Correção")
                    for suggestion in diagnosis['suggestions']:
                        st.info(f"• {suggestion}")
                
                # Explorar dados das tabelas relacionadas
                if diagnosis['table_info']:
                    st.subheader("📋 Informações das Tabelas")
                    for table, info in diagnosis['table_info'].items():
                        with st.expander(f"Tabela: {table} ({info.get('count', 0)} registros)"):
                            st.write("**Colunas disponíveis:**")
                            for i, col in enumerate(info.get('columns', [])):
                                col_type = info.get('types', [''])[i] if i < len(info.get('types', [])) else 'N/A'
                                st.write(f"• {col} ({col_type})")
                
                # Mostrar dados de exemplo se disponíveis
                if diagnosis['sample_data']:
                    st.subheader("📄 Dados de Exemplo")
                    for table, sample in diagnosis['sample_data'].items():
                        with st.expander(f"Exemplos da tabela {table}"):
                            if sample:
                                st.json(sample)
                            else:
                                st.write("Nenhum dado de exemplo disponível")
                
                # Queries sugeridas
                if debug_result['similar_queries']:
                    st.subheader("🔄 Queries Sugeridas para Teste")
                    for i, suggested_query in enumerate(debug_result['similar_queries']):
                        col_btn, col_code = st.columns([1, 3])
                        
                        with col_btn:
                            if st.button(f"Testar", key=f"test_query_{i}"):
                                try:
                                    test_result = st.session_state.db.execute_query(suggested_query)
                                    if test_result is not None and len(test_result) > 0:
                                        st.success(f"✅ Funcionou! ({len(test_result)} registros)")
                                        # Salvar como resultado válido e recarregar página
                                        st.session_state.last_response = {
                                            'success': True,
                                            'data': test_result,
                                            'total_records': len(test_result),
                                            'summary': f"Query sugerida executada com sucesso. Encontrados {len(test_result)} registros.",
                                            'interpretation': {'intencao': 'Query de diagnóstico sugerida'}
                                        }
                                        st.session_state.last_query = suggested_query
                                        st.rerun()
                                    else:
                                        st.warning("Query executou mas não retornou dados")
                                except Exception as test_e:
                                    st.error(f"Query falhou: {test_e}")
                        
                        with col_code:
                            st.code(suggested_query, language="sql")

                st.stop()

            # Formatação da resposta
            response = st.session_state.agents.format_complete_response(
                results, interpretation, user_input
            )

            st.session_state.last_response = response
            st.session_state.last_query = sql_query
            st.session_state.interpretation = interpretation

        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")

            # Debug detalhado do erro
            st.subheader("🔍 Detalhes do Erro:")

            with st.expander("Informações Técnicas", expanded=True):
                st.write("**Erro:**", str(e))

                if 'interpretation' in locals():
                    st.write("**Interpretação gerada:**")
                    st.json(interpretation)

                if 'sql_query' in locals():
                    st.write("**Query SQL gerada:**")
                    st.code(sql_query, language="sql")

                    # Sugerir correções na query
                    st.write("**💡 Possíveis correções:**")
                    st.markdown("""
                    - Verifique se os nomes das colunas existem na tabela
                    - Confirme o formato das datas (YYYY-MM-DD)
                    - Teste filtros mais simples primeiro
                    - Verifique se a tabela tem os dados esperados
                    """)

                # Mostrar schema do banco
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

    if not response["success"]:
        st.markdown(f"""
        <div class="error-box">
            <strong>❌ Erro na análise:</strong><br>
            {response["summary"]}
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Determinar o tipo de saída
    output_type = st.session_state.get('output_type', '🔍 Automático')
    
    if output_type == "🔍 Automático":
        output_type = {
            "tabela": "📋 Tabela",
            "barras": "📊 Gráfico",
            "pizza": "📊 Gráfico",
            "linha": "📊 Gráfico",
            "texto": "📝 Texto"
        }.get(st.session_state.interpretation.get("tipo_grafico", "tabela"), "📋 Tabela")

        # Definir chart_type baseado na interpretação automática
        if output_type == "📊 Gráfico":
            auto_chart_type = st.session_state.interpretation.get("tipo_grafico", "barras")
            chart_type = {
                "barras": "Barras",
                "pizza": "Pizza",
                "linha": "Linha"
            }.get(auto_chart_type, "Barras")

    # Container principal de resultados
    with st.container():
        st.markdown('<div class="output-container">', unsafe_allow_html=True)

        # Cabeçalho da análise
        st.markdown(f'<h2 class="result-title">🔍 Resultados da Análise</h2>', unsafe_allow_html=True)
        st.markdown(f'<p class="result-subtitle">📌 {response["interpretation"]["intencao"]}</p>', unsafe_allow_html=True)

        # Resumo textual
        st.markdown(f"""
        <div class="insight-box">
        {response["summary"]}
        </div>
        """, unsafe_allow_html=True)

        # Exibir informações básicas do resultado
        st.info(f"📊 **{len(response['data'])}** registros encontrados | **{len(response['data'].columns)}** colunas")

        # Container de métricas
        if len(response["data"]) > 0 and len(response["data"].select_dtypes(include=['number']).columns) > 0:
            # Métricas rápidas
            if len(response["data"]) > 0:
                metric_cols = st.columns(3)

                with metric_cols[0]:
                    st.metric(
                        "📋 Total de Registros",
                        f"{response['total_records']:,}",
                        delta=None
                    )

                # Obter colunas relevantes para métricas
                relevant_cols = get_relevant_metric_columns(response["data"])

                if len(relevant_cols) >= 1:
                    with metric_cols[1]:
                        col_name = relevant_cols[0]
                        total_value = response["data"][col_name].sum()
                        display_name = col_name.replace('_', ' ').title()

                        # Formatação especial para valores monetários
                        if 'valor' in col_name.lower() or 'preco' in col_name.lower():
                            st.metric(
                                f"💰 Total {display_name}",
                                f"R$ {total_value:,.2f}",
                                delta=None
                            )
                        else:
                            st.metric(
                                f"📊 Total {display_name}",
                                f"{total_value:,.0f}",
                                delta=None
                            )

                if len(relevant_cols) >= 1:
                    with metric_cols[2]:
                        col_name = relevant_cols[0]
                        avg_value = response["data"][col_name].mean()
                        display_name = col_name.replace('_', ' ').title()

                        # Formatação especial para valores monetários
                        if 'valor' in col_name.lower() or 'preco' in col_name.lower():
                            st.metric(
                                f"📊 Média {display_name}",
                                f"R$ {avg_value:,.2f}",
                                delta=None
                            )
                        else:
                            st.metric(
                                f"📊 Média {display_name}",
                                f"{avg_value:,.2f}",
                                delta=None
                            )

        # Verificar se temos dados para exibir
        if len(response["data"]) == 0:
            st.warning("⚠️ Nenhum resultado encontrado para sua consulta.")
            st.markdown("""
            **Possíveis motivos:**
            - Os critérios de filtro são muito restritivos
            - Os dados solicitados não existem no banco
            - Problema na formatação da data ou outros campos
            """)

            # Mostrar detalhes técnicos automaticamente quando não há resultados
            with st.expander("🔍 Detalhes da Consulta", expanded=True):
                st.subheader("Query SQL Executada:")
                st.code(st.session_state.last_query, language="sql")

                st.subheader("Interpretação da IA:")
                st.json(st.session_state.interpretation)

                # Sugestões de debug
                st.subheader("💡 Sugestões:")
                st.markdown("""
                1. Verifique se os nomes das colunas estão corretos
                2. Confirme se os dados existem no período solicitado
                3. Teste uma consulta mais simples primeiro
                4. Verifique o formato das datas no banco
                """)

            st.stop()

        # Detalhes técnicos (se habilitado)
        if show_debug:
            with st.expander("🔍 Detalhes Técnicos", expanded=True):
                st.subheader("Interpretação")
                st.json(st.session_state.interpretation)

                st.subheader("Query SQL")
                st.code(st.session_state.last_query, language="sql")

                st.subheader("Dados Retornados")
                st.write(f"Linhas: {len(response['data'])}, Colunas: {len(response['data'].columns)}")
                if len(response["data"]) > 0:
                    st.write("Primeiras 5 linhas:")
                    st.dataframe(response["data"].head())

        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📋 Tabela", "📊 Gráfico Matplotlib", "📈 Gráfico Interativo"])

        with tab1:
            st.subheader("📋 Dados Tabulares")

            # Controles de ordenação
            st.markdown('<div class="sort-controls">', unsafe_allow_html=True)
            st.markdown("**🔄 Opções de Ordenação**")

            col_sort1, col_sort2, col_sort3 = st.columns([3, 2, 2])

            with col_sort1:
                # Opções de colunas para ordenação (incluindo "Não ordenar")
                sort_options = ["Não ordenar"] + list(response["data"].columns)
                sort_column = st.selectbox(
                    "📊 Ordenar por coluna:",
                    options=sort_options,
                    key="sort_column_select"
                )

            with col_sort2:
                sort_order = st.selectbox(
                    "🔄 Ordem:",
                    options=["Crescente (menor → maior)", "Decrescente (maior → menor)"],
                    key="sort_order_select")

            with col_sort3:
                # Quantidade de registros para exibir
                display_limit = st.selectbox(
                    "📄 Mostrar registros:",
                    options=[50, 100, 200, 500, "Todos"],
                    index=1,  # Default para 100
                    key="display_limit_select"
                )

            st.markdown('</div>', unsafe_allow_html=True)

            # Aplicar ordenação e limite
            display_df = response["data"].copy()

            # Aplicar ordenação se selecionada
            if sort_column != "Não ordenar":
                display_df = apply_table_sorting(display_df, sort_column, sort_order)

            # Aplicar limite de registros
            if display_limit != "Todos":
                display_df = display_df.head(display_limit)

            # Mostrar informações sobre ordenação e filtragem
            if sort_column != "Não ordenar":
                order_text = "crescente" if "Crescente" in sort_order else "decrescente"
                st.info(f"📊 Tabela ordenada por **{sort_column}** em ordem **{order_text}** | Exibindo **{len(display_df):,}** de **{len(response['data']):,}** registros")
            else:
                st.info(f"📊 Exibindo **{len(display_df):,}** de **{len(response['data']):,}** registros")

            # Exibir tabela
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(500, 35 * len(display_df)) + 40  # Altura dinâmica
            )

            # Botões de download
            col_download1, col_download2 = st.columns(2)

            with col_download1:
                # Download dos dados exibidos (com ordenação aplicada)
                csv_displayed = display_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Exportar Dados Exibidos",
                    csv_displayed,
                    file_name=f"analise_exibida_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Baixe apenas os dados exibidos na tabela (com ordenação aplicada)")

            with col_download2:
                # Download de todos os dados originais
                csv_all = response["data"].to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Exportar Todos os Dados",
                    csv_all,
                    file_name=f"analise_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Baixe todos os dados originais da consulta")

        with tab2:
            st.subheader("📊 Gráfico com Matplotlib")

            # Verificar se temos dados suficientes para gráfico
            if len(response["data"].columns) >= 2 and len(response["data"]) > 0:
                try:
                    fig, ax = plt.subplots(figsize=(10, 6))

                    # Selecionar colunas apropriadas
                    x_col = response["data"].columns[0]
                    y_col = response["data"].columns[1]

                    # Usar os dados com ordenação aplicada se disponível
                    plot_data = response["data"]
                    if 'sort_column_select' in st.session_state and st.session_state.sort_column_select != "Não ordenar":
                        plot_data = apply_table_sorting(
                            response["data"], 
                            st.session_state.get('sort_column_select', ''), 
                            st.session_state.get('sort_order_select', 'Crescente (menor → maior)')
                        )

                    if chart_type == "Barras" or chart_type == "Automático":
                        data_plot = plot_data.head(20)  # Limitar para legibilidade
                        ax.bar(data_plot[x_col], data_plot[y_col])
                        ax.set_xlabel(x_col)
                        ax.set_ylabel(y_col)
                        plt.xticks(rotation=45)

                    elif chart_type == "Pizza":
                        data_plot = plot_data.head(10)  # Limitar para pizza
                        ax.pie(data_plot[y_col], labels=data_plot[x_col], autopct='%1.1f%%')

                    elif chart_type == "Linha":
                        ax.plot(plot_data[x_col], plot_data[y_col], marker='o')
                        ax.set_xlabel(x_col)
                        ax.set_ylabel(y_col)
                        plt.xticks(rotation=45)

                    plt.tight_layout()
                    st.pyplot(fig)

                except Exception as e:
                    st.warning(f"⚠️ Erro ao gerar gráfico matplotlib: {str(e)}")
                    st.info("📋 Exibindo dados em formato tabular")
                    st.dataframe(response["data"])
            else:
                st.warning("⚠️ Dados insuficientes para gerar gráfico")
                st.dataframe(response["data"])

        with tab3:
            st.subheader("📈 Gráfico Interativo (Plotly)")

            # Verificar se temos dados suficientes para gráfico
            if len(response["data"].columns) >= 2 and len(response["data"]) > 0:
                try:
                    # Selecionar colunas apropriadas
                    x_col = response["data"].columns[0]
                    y_col = response["data"].columns[1]

                    # Usar os dados com ordenação aplicada se disponível
                    plot_data = response["data"]
                    if 'sort_column_select' in st.session_state and st.session_state.sort_column_select != "Não ordenar":
                        plot_data = apply_table_sorting(
                            response["data"], 
                            st.session_state.get('sort_column_select', ''), 
                            st.session_state.get('sort_order_select', 'Crescente (menor → maior)')
                        )

                    if chart_type == "Pizza":
                        fig = px.pie(plot_data.head(10), values=y_col, names=x_col)
                    elif chart_type == "Linha":
                        fig = px.line(plot_data, x=x_col, y=y_col)
                    elif chart_type == "Scatter":
                        fig = px.scatter(plot_data, x=x_col, y=y_col)
                    else:  # Barras ou Automático
                        fig = px.bar(plot_data.head(20), x=x_col, y=y_col)

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.warning(f"⚠️ Erro ao gerar gráfico interativo: {str(e)}")
                    st.info("📋 Exibindo dados em formato tabular")
                    st.dataframe(response["data"])
            else:
                st.warning("⚠️ Dados insuficientes para gerar gráfico")
                st.dataframe(response["data"])

        st.markdown('</div>', unsafe_allow_html=True)

# Rodapé com informações do desenvolvedor
st.divider()

# Footer com créditos expandidos
st.markdown("""
<div class="footer">
    <div style="margin-bottom: 1rem;">
        <strong>📊 Analytics com IA - Versão Completa</strong>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <strong>🚀 Desenvolvido por:</strong><br>
            <strong>Filipe Rangel</strong><br>
            <small>Especialista em Analytics e Inteligência Artificial</small>
        </div>
        <div style="text-align: right;">
            <div><strong>📅 Última atualização:</strong> {datetime_str}</div>
            <div><strong>📊 Registros processados:</strong> {records_count:,}</div>
            <div><small>Versão 2.0 - Com IA Integrada</small></div>
        </div>
    </div>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color); text-align: center;">
        <small>
            Esta aplicação utiliza tecnologias de ponta em IA para análise de dados.<br>
            Desenvolvida com Streamlit, OpenAI GPT, e Python para proporcionar insights inteligentes.
        </small>
    </div>
</div>
""".format(
    datetime_str=datetime.now().strftime('%d/%m/%Y %H:%M'),
    records_count=st.session_state.get('last_response', {}).get('total_records', 0)
), unsafe_allow_html=True)