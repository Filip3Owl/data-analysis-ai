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

# CSS customizado melhorado
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
    
    /* Botões da sidebar */
    .stButton button {
        width: 100% !important;
        text-align: left !important;
        background-color: var(--card-bg) !important;
        color: var(--dark-text) !important;
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
        color: var(--dark-text) !important;
    }
    
    /* Subheaders da sidebar */
    .css-1d391kg h2, .css-1d391kg h3 {
        color: var(--dark-text) !important;
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

    # Exemplos de consultas - EXPANDIDOS
    st.subheader("💡 Exemplos de Consultas")
    exemplos = {
        "Top 10 clientes por vendas": "📋 Tabela",
        "Clientes por estado": "📊 Gráfico",
        "Vendas dos últimos 30 dias": "📊 Gráfico",
        "Resumo geral de clientes": "📝 Texto",
        "Clientes que compraram via app": "📋 Tabela",
        "5 estados com mais clientes via app em maio": "📋 Tabela",
        "Clientes em campanhas WhatsApp 2024": "📋 Tabela",
        "Categorias com mais compras por cliente": "📊 Gráfico",
        "Reclamações não resolvidas por canal": "📊 Gráfico",
        "Evolução de vendas mensais": "📊 Gráfico",
        "Top 10 produtos mais vendidos": "📋 Tabela",
        "Distribuição de clientes por idade": "📊 Gráfico",
        "Análise de satisfação por região": "📊 Gráfico"
    }

    # Organizar exemplos em categorias
    st.markdown("**📊 Análises de Vendas:**")
    vendas_exemplos = {k: v for k, v in exemplos.items() if any(
        palavra in k.lower() for palavra in ['vendas', 'produto', 'top', 'cliente'])}

    for exemplo, tipo in vendas_exemplos.items():
        if st.button(f"{tipo} {exemplo}", key=f"exemplo_vendas_{exemplo}"):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo

    st.markdown("**📱 Análises de Canais:**")
    canais_exemplos = {k: v for k, v in exemplos.items() if any(
        palavra in k.lower() for palavra in ['app', 'whatsapp', 'canal', 'reclamações'])}

    for exemplo, tipo in canais_exemplos.items():
        if st.button(f"{tipo} {exemplo}", key=f"exemplo_canais_{exemplo}"):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo

    st.markdown("**🌍 Análises Geográficas:**")
    geo_exemplos = {k: v for k, v in exemplos.items() if any(
        palavra in k.lower() for palavra in ['estado', 'região', 'distribuição'])}

    for exemplo, tipo in geo_exemplos.items():
        if st.button(f"{tipo} {exemplo}", key=f"exemplo_geo_{exemplo}"):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo

    st.markdown("**📈 Análises Temporais:**")
    tempo_exemplos = {k: v for k, v in exemplos.items() if any(palavra in k.lower(
    ) for palavra in ['maio', '2024', 'evolução', 'mensais', 'dias'])}

    for exemplo, tipo in tempo_exemplos.items():
        if st.button(f"{tipo} {exemplo}", key=f"exemplo_tempo_{exemplo}"):
            st.session_state.exemplo_selecionado = exemplo
            st.session_state.output_type = tipo

# Interface principal
st.header("🎯 Faça sua Análise")

# Inicializar output_type se não existir
if 'output_type' not in st.session_state:
    st.session_state.output_type = "🔍 Automático"

output_type = st.session_state.get('output_type', "🔍 Automático")

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
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)

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

    # Limpar exemplo selecionado
    if 'exemplo_selecionado' in st.session_state:
        del st.session_state.exemplo_selecionado

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
            # Pré-processar a consulta do usuário
            processed_input = preprocess_user_query(user_input)

            # Interpretação da solicitação
            interpretation = st.session_state.agents.interpret_request(
                processed_input)

            # Determinar o tipo de saída com base no prompt do usuário
            if "tabela" in user_input.lower() or "lista" in user_input.lower():
                output_type = "📋 Tabela"
            elif "gráfico" in user_input.lower() or "grafico" in user_input.lower():
                output_type = "📊 Gráfico"
            elif "resumo" in user_input.lower() or "texto" in user_input.lower():
                output_type = "📝 Texto"
            else:
                output_type = "🔍 Automático"

            # Sobrescrever tipo de saída se não for automático
            if output_type != "🔍 Automático":
                interpretation["tipo_grafico"] = {
                    "📋 Tabela": "tabela",
                    "📊 Gráfico": "barras",  # Definir como barras por padrão
                    "📝 Texto": "texto"
                }[output_type]

            # Geração SQL
            sql_query = st.session_state.agents.generate_sql(interpretation)

            # Executação da query
            results = st.session_state.db.execute_query(sql_query)

            # Debug: mostrar resultados brutos se não há dados
            if results is None or (isinstance(results, pd.DataFrame) and len(results) == 0):
                st.warning(
                    "⚠️ A consulta não retornou dados. Verificando possíveis problemas...")

                # Mostrar a query para debug
                st.code(sql_query, language="sql")

                # Tentar queries de diagnóstico
                try:
                    # Verificar se existem dados na tabela principal
                    test_query = "SELECT COUNT(*) as total FROM clientes LIMIT 1"
                    test_result = st.session_state.db.execute_query(test_query)
                    if test_result is not None and len(test_result) > 0:
                        st.info(
                            f"Total de registros na tabela clientes: {test_result.iloc[0]['total']}")

                    # Verificar estrutura da tabela
                    schema_query = "PRAGMA table_info(clientes)"
                    schema_result = st.session_state.db.execute_query(
                        schema_query)
                    if schema_result is not None and len(schema_result) > 0:
                        st.write("Estrutura da tabela:")
                        st.dataframe(schema_result)

                    # Verificar dados de exemplo
                    sample_query = "SELECT * FROM clientes LIMIT 5"
                    sample_result = st.session_state.db.execute_query(
                        sample_query)
                    if sample_result is not None and len(sample_result) > 0:
                        st.write("Dados de exemplo:")
                        st.dataframe(sample_result)

                except Exception as debug_e:
                    st.error(f"Erro no diagnóstico: {debug_e}")

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
                except:
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

    # Determinar o tipo de saída com base no prompt do usuário
    if "tabela" in user_input.lower() or "lista" in user_input.lower():
        output_type = "📋 Tabela"
    elif "gráfico" in user_input.lower() or "grafico" in user_input.lower():
        output_type = "📊 Gráfico"
    elif "resumo" in user_input.lower() or "texto" in user_input.lower():
        output_type = "📝 Texto"
    else:
        output_type = "📋 Tabela"  # Padrão para tabela se não for especificado

    # Container principal de resultados
    with st.container():
        st.markdown('<div class="output-container">', unsafe_allow_html=True)

        # Cabeçalho da análise
        st.markdown(
            f'<h2 class="result-title">🔍 Resultados da Análise</h2>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="result-subtitle">📌 {response["interpretation"]["intencao"]}</p>', unsafe_allow_html=True)

        # Resumo textual
        st.markdown(f"""
        <div class="insight-box">
        {response["summary"]}
        </div>
        """, unsafe_allow_html=True)

        # Exibir informações básicas do resultado
        st.info(
            f"📊 **{len(response['data'])}** registros encontrados | **{len(response['data'].columns)}** colunas")

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

        # Exibir resultados com base no tipo de saída determinado
        if output_type == "📋 Tabela":
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
                    key="sort_order_select"
                )
            
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

            # Formatação especial para valores monetários (mantida para exibição)
            formatted_df = display_df.copy()
            for col in formatted_df.select_dtypes(include=['number']).columns:
                if 'valor' in col.lower() or 'preco' in col.lower():
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"R$ {x:,.2f}")
                elif 'count' in col.lower() or col.lower().endswith('_count'):
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{x:,.0f}")
                elif not any(pattern in col.lower() for pattern in ['id', 'idade']):
                    # Aplicar formatação numérica apenas para colunas relevantes
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{x:,.2f}" if x != int(x) else f"{x:,.0f}")

            # Exibir tabela
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(500, 35 * len(display_df)) + 40) # Altura dinâmica

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
                    help="Baixe apenas os dados exibidos na tabela (com ordenação aplicada)"
                )
            
            with col_download2:
                # Download de todos os dados originais
                csv_all = response["data"].to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Exportar Todos os Dados",
                    csv_all,
                    file_name=f"analise_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Baixe todos os dados originais da consulta"
                )

        elif output_type == "📊 Gráfico":
            st.subheader("📊 Visualização Gráfica")

            # Verificar se temos dados suficientes para gráfico
            if len(response["data"].columns) >= 2 and len(response["data"]) > 0:
                try:
                    # Selecionar colunas apropriadas
                    x_col = response["data"].columns[0]
                    y_col = response["data"].columns[1]

                    # Determinar o tipo de gráfico mais apropriado
                    if len(response["data"]) > 10 and response["data"][x_col].dtype in ['object', 'string']:
                        # Para muitos itens categóricos, usar gráfico de barras
                        fig = px.bar(response["data"].head(20), x=x_col, y=y_col)
                    elif len(response["data"]) <= 10 and response["data"][x_col].dtype in ['object', 'string']:
                        # Para poucos itens categóricos, usar gráfico de pizza
                        fig = px.pie(response["data"], values=y_col, names=x_col)
                    elif pd.api.types.is_datetime64_any_dtype(response["data"][x_col]):
                        # Para dados temporais, usar gráfico de linha
                        fig = px.line(response["data"], x=x_col, y=y_col)
                    else:
                        # Padrão para gráfico de barras
                        fig = px.bar(response["data"].head(20), x=x_col, y=y_col)

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.warning(
                        f"⚠️ Erro ao gerar gráfico interativo: {str(e)}")
                    st.info("📋 Exibindo dados em formato tabular")
                    st.dataframe(response["data"])
            else:
                st.warning("⚠️ Dados insuficientes para gerar gráfico")
                st.dataframe(response["data"])

        elif output_type == "📝 Texto":
            st.subheader("📝 Resumo Textual")
            st.write(response["summary"])

        st.markdown('</div>', unsafe_allow_html=True)

# Rodapé
st.divider()
st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
           f"📊 {st.session_state.get('last_response', {}).get('total_records', 0)} registros")