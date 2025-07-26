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

# CSS customizado corrigido
st.markdown("""
<style>
    :root {
        --primary: #667eea;
        --secondary: #764ba2;
        --light-bg: #f8fafc;
        --dark-text: #1e293b;
        --light-text: #f8fafc;
    }
    
    body {
        color: var(--dark-text);
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
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    .stTextArea textarea {
        background-color: white !important;
        color: var(--dark-text) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    .stTextArea label {
        color: var(--dark-text) !important;
        font-weight: 600 !important;
    }
    
    .output-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    
    .text-output {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        margin-bottom: 1rem;
        color: var(--dark-text);
    }
    
    .table-output {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin: 1rem 0;
        background: white;
    }
    
    .dataframe {
        width: 100% !important;
        color: var(--dark-text) !important;
    }
    
    .dataframe th {
        background-color: var(--primary) !important;
        color: var(--light-text) !important;
        position: sticky;
        top: 0;
        font-weight: 600;
    }
    
    .dataframe td {
        background-color: white !important;
        color: var(--dark-text) !important;
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
    
    .stButton>button:hover {
        background-color: #5a6ec5;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .error-box {
        background-color: #fee2e2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        margin: 1rem 0;
        color: #b91c1c;
    }
    
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    .stTextArea textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    
    .result-title {
        color: var(--dark-text);
        margin-bottom: 0.5rem;
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
    
    # Container principal
    with st.container():
        st.markdown(f'<div class="output-card">', unsafe_allow_html=True)
        
        # Cabeçalho da análise
        st.subheader("🔍 Resultados da Análise")
        st.caption(f"📌 {response['interpretation']['intencao']}")
        
        # Exibir conforme o tipo selecionado
        if output_type == "📋 Tabela":
            st.markdown('<div class="table-output">', unsafe_allow_html=True)
            
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
                height=min(500, 35 * len(display_df) + 40  # Altura dinâmica
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
                    # Selecionar gráfico apropriado
                    if chart_type == "Barras":
                        fig = px.bar(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            title=response["interpretation"]["intencao"],
                            color=response["data"].columns[0],
                            text=response["data"].columns[1]
                        )
                        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                    
                    elif chart_type == "Pizza":
                        fig = px.pie(
                            response["data"],
                            values=response["data"].columns[1],
                            names=response["data"].columns[0],
                            title=response["interpretation"]["intencao"],
                            hole=0.3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                    
                    elif chart_type == "Linha":
                        fig = px.line(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            title=response["interpretation"]["intencao"],
                            markers=True
                        )
                    
                    elif chart_type == "Área":
                        fig = px.area(
                            response["data"],
                            x=response["data"].columns[0],
                            y=response["data"].columns[1],
                            title=response["interpretation"]["intencao"]
                        )
                    
                    else:  # Histograma
                        fig = px.histogram(
                            response["data"],
                            x=response["data"].columns[0],
                            title=response["interpretation"]["intencao"],
                            nbins=20
                        )
                    
                    fig.update_layout(
                        hovermode="x unified",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico: {str(e)}")
                    st.dataframe(response["data"])
        
        elif output_type == "📝 Texto":
            st.markdown('<div class="text-output">', unsafe_allow_html=True)
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