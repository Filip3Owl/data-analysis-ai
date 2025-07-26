import sys
import os
from pathlib import Path
import streamlit as st
from src.agents import AgentsManager  # Usar o AgentsManager melhorado
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

# CSS customizado para melhor aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .insight-box {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #2c3e50;
    }
    
    .error-box {
        background: #fff5f5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #e53e3e;
        margin: 1rem 0;
        color: #721c24;
    }
    
    .table-container {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
        border-radius: 8px;
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
    <p>Análise inteligente com tabelas, resumos e visualizações interativas</p>
</div>
""", unsafe_allow_html=True)

# Verificação do banco de dados
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'

# Função de diagnóstico rápido
@st.cache_data
def quick_database_check():
    """Verificação rápida do banco de dados com cache."""
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

# Verificar banco
db_ok, db_message = quick_database_check()

if not db_ok:
    st.error(f"❌ **Problema no banco de dados**: {db_message}")
    
    with st.expander("🔧 Diagnóstico Detalhado"):
        st.write("Execute o diagnóstico para identificar problemas específicos:")
        if st.button("Executar Diagnóstico"):
            try:
                with DatabaseManager(str(DB_PATH)) as db:
                    schema = db.get_database_schema()
                    st.json(schema)
            except Exception as e:
                st.error(f"Erro no diagnóstico: {e}")
    
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
    
    # Configuração da API
    openai_key = os.getenv("OPENAI_API_KEY", "")
    key_input = st.text_input(
        "🔑 Chave OpenAI",
        type="password",
        value=openai_key,
        help="Insira sua chave da OpenAI (sk-...)",
        placeholder="sk-..."
    )
    openai_key = key_input or openai_key
    
    # Status da chave
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
    
    # Informações do banco - CORRIGIDO
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
    exemplos = [
        "Top 10 estados com mais clientes",
        "Vendas por categoria em 2024",
        "Evolução mensal de vendas",
        "Clientes que mais compraram", 
        "Distribuição por canal de venda",
        "Suporte por tipo de contato",
        "Efetividade das campanhas",
        "Ticket médio por região"
    ]
    
    for exemplo in exemplos:
        if st.button(f"📝 {exemplo}", key=f"ex_{exemplo}"):
            st.session_state.exemplo_selecionado = exemplo

# Interface principal
st.header("🎯 Faça sua Análise")

# Campo de entrada com exemplo selecionado
pergunta_default = st.session_state.get('exemplo_selecionado', '')
user_input = st.text_area(
    "💬 Descreva o que você quer analisar:",
    value=pergunta_default,
    height=100,
    placeholder="Ex: Mostre o ranking dos 5 estados com mais vendas em 2024"
)

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
            # 1. Interpretação
            interpretation = st.session_state.agents.interpret_request(user_input)
            
            # 2. Geração SQL
            sql_query = st.session_state.agents.generate_sql(interpretation)
            
            # 3. Execução da query
            results = st.session_state.db.execute_query(sql_query)
            
            # 4. Formatação completa da resposta
            response = st.session_state.agents.format_complete_response(
                results, interpretation, user_input
            )
            
            # Armazenar resultados na sessão
            st.session_state.last_response = response
            st.session_state.last_query = sql_query
            st.session_state.last_interpretation = interpretation
            
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            if show_debug and 'last_query' in st.session_state:
                st.code(st.session_state.last_query, language="sql")
            st.stop()

# Exibição dos resultados
if 'last_response' in st.session_state:
    response = st.session_state.last_response
    
    if response["success"]:
        # Layout em colunas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("📊 Resultados da Análise")
            
            # Resumo textual - CORRIGIDO
            st.markdown(f"""
            <div class="insight-box">
            {response["summary"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas rápidas - CORRIGIDO
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
        
        with col2:
            # Detalhes técnicos (se habilitado)
            if show_debug:
                with st.expander("🔍 Detalhes Técnicos", expanded=True):
                    st.subheader("Interpretação")
                    st.json(st.session_state.last_interpretation)
                    
                    st.subheader("Query SQL")
                    st.code(st.session_state.last_query, language="sql")
        
        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📋 Tabela", "📊 Gráfico Matplotlib", "📈 Gráfico Interativo"])
        
        with tab1:
            st.subheader("📋 Dados Tabulares")
            
            # Tabela com paginação
            if len(response["data"]) > 50:
                st.warning(f"⚠️ Mostrando 50 de {len(response['data'])} registros")
                display_df = response["data"].head(50)
            else:
                display_df = response["data"]
            
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
                formatted_df,
                use_container_width=True,
                height=400
            )
            
            # Download dos dados
            csv = response["data"].to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with tab2:
            st.subheader("📊 Visualização Estática")
            
            if response["matplotlib_fig"] is not None:
                st.pyplot(response["matplotlib_fig"])
            else:
                st.info("🔍 Gráfico não disponível para este tipo de dados")
        
        with tab3:
            st.subheader("📈 Visualização Interativa")
            
            if response["plotly_fig"] is not None:
                st.plotly_chart(response["plotly_fig"], use_container_width=True)
            else:
                # Criar gráfico básico com Plotly se não houver
                if len(response["data"]) > 0 and len(response["data"].columns) >= 2:
                    try:
                        x_col = response["data"].columns[0]
                        y_col = response["data"].columns[1]
                        
                        if chart_type.lower() == "pizza":
                            fig = px.pie(response["data"], values=y_col, names=x_col)
                        elif chart_type.lower() == "linha":
                            fig = px.line(response["data"], x=x_col, y=y_col, markers=True)
                        else:
                            fig = px.bar(response["data"], x=x_col, y=y_col)
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.info(f"🔍 Não foi possível gerar gráfico: {e}")
                else:
                    st.info("🔍 Dados insuficientes para gráfico")
    
    else:
        # Erro na resposta - CORRIGIDO
        st.markdown(f"""
        <div class="error-box">
        {response["summary"]}
        </div>
        """, unsafe_allow_html=True)

# Rodapé
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🤖 **Sistema de IA**: Análise inteligente de dados")

with col2:
    st.caption("📊 **Tecnologias**: Streamlit + LangChain + OpenAI")

with col3:
    if 'last_response' in st.session_state:
        st.caption(f"⏱️ **Última análise**: {st.session_state.last_response['total_records']} registros")