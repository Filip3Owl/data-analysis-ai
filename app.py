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
# Substitua a parte do CSS por este código:

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
    
    # Tipo de saída desejada
    st.subheader("📤 Tipo de Saída")
    output_type = st.radio(
        "Selecione o formato de saída:",
        ["📋 Tabela", "📊 Gráfico", "📝 Texto", "🔍 Automático"],
        index=3,
        help="Escolha o formato que deseja receber os resultados"
    )
    
    # Inicializar chart_type com valor padrão
    chart_type = "Barras"
    
    # Opções específicas para gráficos
    if output_type == "📊 Gráfico":
        chart_type = st.selectbox(
            "Tipo de gráfico:",
            ["Barras", "Pizza", "Linha", "Área", "Histograma"],
            index=0
        )
    
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

# Container para área de entrada
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Campo de entrada com exemplo selecionado
    pergunta_default = st.session_state.get('exemplo_selecionado', '')
    output_type = st.session_state.get('output_type', output_type)
    
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

# Botão de análise centralizado
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🚀 Analisar Dados", type="primary", disabled=not api_configured):
        if not user_input.strip():
            st.warning("⚠️ Por favor, descreva sua análise!")
            st.stop()
        
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
        
        # Container de métricas
        if len(response["data"].select_dtypes(include=['number']).columns) > 0:
            numeric_cols = response["data"].select_dtypes(include=['number']).columns
            total_value = response["data"][numeric_cols[0]].sum()
            avg_value = response["data"][numeric_cols[0]].mean()
            count_value = len(response["data"])
            
            st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📋 Total Registros</h4>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0;">{count_value:,}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>💰 Total {numeric_cols[0].replace('_', ' ').title()}</h4>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0;">R$ {total_value:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📊 Média {numeric_cols[0].replace('_', ' ').title()}</h4>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0;">R$ {avg_value:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Exibir conforme o tipo selecionado
        if output_type == "📋 Tabela":
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            
            # Formatar DataFrame para exibição
            display_df = response["data"].copy()
            
            # Tratar valores nulos
            display_df = display_df.fillna('')
            
            # Formatar colunas numéricas
            for col in display_df.select_dtypes(include=['number']).columns:
                if 'valor' in col.lower() or 'total' in col.lower():
                    display_df[col] = display_df[col].apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else '')
                elif 'data' in col.lower():
                    try:
                        display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d/%m/%Y')
                    except:
                        pass
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(500, 35 * len(display_df)) + 40  # Altura dinâmica
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Botão de download
            csv = response["data"].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 Exportar para CSV",
                csv,
                file_name=f"analise_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Baixe os dados completos em formato CSV"
            )
        
        elif output_type == "📊 Gráfico":
            # Verificar se temos dados suficientes
            if len(response["data"].columns) < 2:
                st.warning("⚠️ Dados insuficientes para gerar o gráfico (necessário pelo menos 2 colunas)")
                st.dataframe(response["data"])
            else:
                try:
                    # Determinar automaticamente o melhor tipo de gráfico se for automático
                    if output_type == "🔍 Automático":
                        if len(response["data"]) <= 10 and pd.api.types.is_numeric_dtype(response["data"].iloc[:, 1]):
                            chart_type = "Pizza"
                        elif pd.api.types.is_datetime64_any_dtype(response["data"].iloc[:, 0]):
                            chart_type = "Linha"
                        else:
                            chart_type = "Barras"

                    # Configurações comuns
                    common_args = {
                        'title': response["interpretation"]["intencao"],
                        'labels': {col: col.replace('_', ' ').title() for col in response["data"].columns}
                    }

                    if chart_type == "Barras":
                        fig = px.bar(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            color=response["data"].columns[0],
                            text=response["data"].columns[1],
                            **common_args
                        )
                        fig.update_traces(
                            texttemplate='%{text:.2s}', 
                            textposition='outside',
                            marker_line_color='#1e293b',
                            marker_line_width=0.5
                        )
                        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

                    elif chart_type == "Pizza":
                        fig = px.pie(
                            response["data"],
                            values=response["data"].columns[1],
                            names=response["data"].columns[0],
                            hole=0.3,
                            **common_args
                        )
                        fig.update_traces(
                            textposition='inside', 
                            textinfo='percent+label',
                            marker_line_color='#1e293b',
                            marker_line_width=0.5
                        )

                    elif chart_type == "Linha":
                        fig = px.line(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            markers=True,
                            **common_args
                        )
                        fig.update_traces(line_width=2.5)

                    elif chart_type == "Área":
                        fig = px.area(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            **common_args
                        )

                    else:  # Histograma
                        fig = px.histogram(
                            response["data"],
                            x=response["data"].columns[0],
                            nbins=20,
                            **common_args
                        )

                    # Layout consistente
                    fig.update_layout(
                        font=dict(color='#1e293b', size=12),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        xaxis=dict(showgrid=True, gridcolor='#e2e8f0'),
                        yaxis=dict(showgrid=True, gridcolor='#e2e8f0'),
                        margin=dict(l=20, r=20, t=60, b=20),
                        hoverlabel=dict(
                            bgcolor="white",
                            font_size=12,
                            font_family="sans-serif"
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao gerar gráfico: {str(e)}")
                    st.dataframe(response["data"])
        
        elif output_type == "📝 Texto":
            st.markdown('<div class="summary-container">', unsafe_allow_html=True)
            st.markdown(response["summary"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Detalhes técnicos (expandível)
        with st.expander("🔧 Detalhes Técnicos", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Interpretação")
                st.json(st.session_state.interpretation)
            
            with col2:
                st.subheader("Query SQL")
                st.code(st.session_state.last_query, language="sql")
            
            st.subheader("Dados Brutos")
            st.dataframe(response["data"].head(10))

# Rodapé
st.divider()
st.caption(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
           f"📊 {st.session_state.get('last_response', {}).get('total_records', 0)} registros")