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
        --dark-text: #ffffff;  /* Texto branco */
        --light-text: #f8fafc;
        --card-bg: #2d3748;    /* Cinza escuro para cards */
        --container-bg: #4a5568; /* Cinza médio para containers */
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
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        color: var(--dark-text);
    }
    
    .output-container {
        background-color: var(--container-bg);
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
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
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 1rem 0;
        background-color: var(--container-bg);
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
        background-color: var(--container-bg) !important;
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
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: var(--container-bg);
    }
    
    .st-expander .st-expanderHeader {
        color: var(--dark-text);
        font-weight: 600;
    }
    
    .st-expander .st-expanderContent {
        color: var(--dark-text);
    }
    
    .schema-info {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.25rem 0;
        font-size: 0.85rem;
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
                    st.write("**Colunas:**")
                    columns = table_info.get('columns', [])
                    types = table_info.get('types', [])
                    
                    if columns:
                        for i, col in enumerate(columns):
                            col_type = types[i] if i < len(types) else "N/A"
                            st.markdown(f"<div class='schema-info'>• <strong>{col}</strong> ({col_type})</div>", 
                                      unsafe_allow_html=True)
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
    
    # Exemplos de consultas
    st.subheader("💡 Exemplos de Consultas")
    exemplos = {
        "Top 10 clientes": "📋 Tabela",
        "Distribuição por estado": "📊 Gráfico",
        "Resumo de vendas": "📝 Texto",
        "Evolução mensal": "📊 Gráfico"
    }
    
    for exemplo, tipo in exemplos.items():
        if st.button(f"{tipo} {exemplo}", key=f"exemplo_{exemplo}"):
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
    
    st.markdown('<h3 class="result-title">Descreva o que você quer analisar:</h3>', unsafe_allow_html=True)
    
    user_input = st.text_area(
        " ",
        value=pergunta_default,
        height=100,
        placeholder="Ex: Mostre os 10 clientes que mais compraram em formato de tabela",
        help="Descreva sua análise em linguagem natural. Ex: 'Top 5 estados com mais vendas'",
        label_visibility="collapsed"
    )
    
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

# Função para identificar colunas relevantes para métricas
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
            # Interpretação da solicitação
            interpretation = st.session_state.agents.interpret_request(user_input)
            
            # Sobrescrever tipo de saída se não for automático
            if output_type != "🔍 Automático":
                interpretation["tipo_grafico"] = {
                    "📋 Tabela": "tabela",
                    "📊 Gráfico": chart_type.lower(),
                    "📝 Texto": "texto"
                }[output_type]
            
            # Geração SQL
            sql_query = st.session_state.agents.generate_sql(interpretation)
            
            # Execução da query
            results = st.session_state.db.execute_query(sql_query)
            
            # Formatação da resposta
            response = st.session_state.agents.format_complete_response(
                results, interpretation, user_input
            )
            
            st.session_state.last_response = response
            st.session_state.last_query = sql_query
            st.session_state.interpretation = interpretation
            
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            if show_debug and 'last_query' in st.session_state:
                st.code(st.session_state.last_query, language="sql")
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
        
        # Container de métricas
        if len(response["data"].select_dtypes(include=['number']).columns) > 0:
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
        
        # Detalhes técnicos (se habilitado)
        if show_debug:
            with st.expander("🔍 Detalhes Técnicos", expanded=True):
                st.subheader("Interpretação")
                st.json(st.session_state.interpretation)
                
                st.subheader("Query SQL")
                st.code(st.session_state.last_query, language="sql")
        
        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📋 Tabela", "📊 Gráfico Matplotlib", "📈 Gráfico Interativo"])
        
        with tab1:
            st.subheader("📋 Dados Tabulares")
            
            # Preparar dados para exibição
            display_df = response["data"].head(100)  # Limitar a 100 linhas para performance
            
            # Formatação especial para valores monetários
            formatted_df = display_df.copy()
            for col in formatted_df.select_dtypes(include=['number']).columns:
                if 'valor' in col.lower() or 'preco' in col.lower():
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"R$ {x:,.2f}")
                elif 'count' in col.lower() or col.lower().endswith('_count'):
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}")
                elif not any(pattern in col.lower() for pattern in ['id', 'idade']):
                    # Aplicar formatação numérica apenas para colunas relevantes
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.2f}" if x != int(x) else f"{x:,.0f}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(500, 35 * len(display_df)) + 40  # Altura dinâmica
            )
            
            # Botão de download
            csv = response["data"].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 Exportar para CSV",
                csv,
                file_name=f"analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Baixe os dados completos em formato CSV"
            )
        
        with tab2:
            st.subheader("📊 Gráfico com Matplotlib")
            
            # Verificar se temos dados suficientes para gráfico
            if len(response["data"].columns) >= 2 and len(response["data"]) > 0:
                try:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Selecionar colunas apropriadas
                    x_col = response["data"].columns[0]
                    y_col = response["data"].columns[1]
                    
                    if chart_type == "Barras" or chart_type == "Automático":
                        data_plot = response["data"].head(20)  # Limitar para legibilidade
                        ax.bar(data_plot[x_col], data_plot[y_col])
                        ax.set_xlabel(x_col)
                        ax.set_ylabel(y_col)
                        plt.xticks(rotation=45)
                        
                    elif chart_type == "Pizza":
                        data_plot = response["data"].head(10)  # Limitar para pizza
                        ax.pie(data_plot[y_col], labels=data_plot[x_col], autopct='%1.1f%%')
                        
                    elif chart_type == "Linha":
                        ax.plot(response["data"][x_col], response["data"][y_col], marker='o')
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
                    
                    if chart_type == "Pizza":
                        fig = px.pie(response["data"].head(10), values=y_col, names=x_col)
                    elif chart_type == "Linha":
                        fig = px.line(response["data"], x=x_col, y=y_col)
                    elif chart_type == "Scatter":
                        fig = px.scatter(response["data"], x=x_col, y=y_col)
                    else:  # Barras ou Automático
                        fig = px.bar(response["data"].head(20), x=x_col, y=y_col)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.warning(f"⚠️ Erro ao gerar gráfico interativo: {str(e)}")
                    st.info("📋 Exibindo dados em formato tabular")
                    st.dataframe(response["data"])
            else:
                st.warning("⚠️ Dados insuficientes para gerar gráfico")
                st.dataframe(response["data"])
        
        st.markdown('</div>', unsafe_allow_html=True)

# Rodapé
st.divider()
st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
           f"📊 {st.session_state.get('last_response', {}).get('total_records', 0)} registros")