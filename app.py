import sys
import os
from pathlib import Path
import streamlit as st
from src.agents import AgentsManager
from src.database import DatabaseManager
from src.utils import generate_visualization, detect_chart_type
from langchain.llms import OpenAI
from dotenv import load_dotenv
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).parent.resolve()  # Pasta onde app.py está
sys.path.append(str(PROJECT_ROOT))  # Adiciona ao Python path


# Configuração inicial
load_dotenv()
st.set_page_config(page_title="Analytics com IA", layout="wide")
st.title("📊 Analytics com IA")

# Caminho do banco de dados (com verificação)
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'
if not DB_PATH.exists():
    st.error(f"Arquivo do banco de dados não encontrado em: {DB_PATH}")
    st.stop()

# Sidebar - Configurações aprimoradas
with st.sidebar:
    st.header("Configurações")
    
    # Sistema de chave com fallback inteligente
    openai_key = os.getenv("OPENAI_API_KEY", "")
    key_input = st.text_input(
        "Chave da OpenAI",
        type="password",
        value=openai_key,
        help="Insira sua chave da OpenAI ou configure no arquivo .env"
    )
    openai_key = key_input or openai_key  # Prioriza a chave do input
    
    # Status da chave
    if openai_key:
        if openai_key and openai_key.startswith('sk-'):
            st.success("Chave configurada ✔️")
        else:
            st.warning("Formato de chave inválido")
    else:
        st.error("Chave não configurada")

    st.markdown("""
    ### Exemplos de consultas:
    - "Liste os 5 estados com mais clientes"
    - "Mostre vendas por categoria como gráfico"
    - "Qual o ticket médio por canal?"
    - "Reclamações não resolvidas por canal"
    """)

# Inicialização do sistema com tratamento de erros
try:
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager(str(DB_PATH))
        if not st.session_state.db.connect():
            st.error("Falha ao conectar ao banco de dados")
            st.stop()

    if "llm" not in st.session_state:
        if openai_key and openai_key.startswith('sk-'):
            st.session_state.llm = OpenAI(
                openai_api_key=openai_key,
                temperature=0.3,
                max_tokens=1500,
                model="gpt-3.5-turbo-instruct"
            )
            st.session_state.agents = AgentsManager(st.session_state.llm)
            st.success("Sistema de IA inicializado!")
        else:
            st.session_state.llm = None
except Exception as e:
    st.error(f"Falha na inicialização: {str(e)}")
    st.stop()

# Interface principal
user_input = st.text_area("Faça sua pergunta sobre os dados:", height=100)

if st.button("Analisar") and user_input:
    if not openai_key or not openai_key.startswith('sk-'):
        st.error("Configure uma chave válida da OpenAI")
        st.stop()
    
    if not st.session_state.get('llm'):
        st.error("Sistema de IA não inicializado")
        st.stop()

    with st.spinner("Processando sua solicitação..."):
        try:
            # Container para resultados
            main_col, debug_col = st.columns([3, 1])
            
            with main_col:
                # Fluxo de processamento
                interpretation = st.session_state.agents.interpret_request(user_input)
                sql_query = st.session_state.agents.generate_sql(interpretation)
                results = st.session_state.db.execute_query(sql_query)
                
                # Exibição principal
                st.subheader("Resultados")
                if not results.empty:
                    response = st.session_state.agents.format_response(
                        results.to_json(orient='records', force_ascii=False), 
                        user_input
                    )
                    st.markdown(response)
                    
                    # Visualização automática
                    chart_type = detect_chart_type(user_input)
                    if chart_type != "text":
                        fig = generate_visualization(results, chart_type)
                        if fig:
                            st.pyplot(fig)
                else:
                    st.warning("Nenhum resultado encontrado")
            
            # Painel de debug
            with debug_col.expander("💻 Detalhes técnicos"):
                st.caption("Interpretação:")
                st.json(interpretation)
                st.caption("Query SQL:")
                st.code(sql_query, language="sql")
                st.caption("Dados brutos (amostra):")
                st.dataframe(results.head(3) if not results.empty else pd.DataFrame())

        except Exception as e:
            st.error(f"Erro durante o processamento: {str(e)}")
            st.exception(e)

# Rodapé
st.divider()
st.caption("Sistema de análise com IA v2.0 | Desenvolvido com Streamlit e LangChain")