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

# Configuração de caminhos
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

# Configuração inicial
load_dotenv()
st.set_page_config(page_title="Analytics com IA", layout="wide")
st.title("📊 Analytics com IA")

# Verificação do banco de dados
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'
if not DB_PATH.exists():
    st.error(f"Arquivo do banco de dados não encontrado em: {DB_PATH}")
    st.stop()

# Inicialização do sistema
try:
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager(str(DB_PATH))
        if not st.session_state.db.connect():
            st.error("Falha ao conectar ao banco de dados")
            st.stop()

    # Verificação do banco (agora que db está inicializado)
    with st.expander("🔍 Verificação Rápida do Banco de Dados"):
        if st.button("Testar conexão com tabelas"):
            test_queries = {
                "Clientes": "SELECT * FROM clientes LIMIT 5",
                "Compras": "SELECT * FROM compras LIMIT 5",
                "Suporte": "SELECT * FROM suporte LIMIT 5",
                "Campanhas": "SELECT * FROM campanhas_marketing LIMIT 5"
            }
            
            for nome, query in test_queries.items():
                st.subheader(nome)
                df = st.session_state.db.execute_query(query)
                if not df.empty:
                    st.dataframe(df)
                else:
                    st.error(f"Nenhum dado encontrado na tabela {nome}")
                    st.code(query)

except Exception as e:
    st.error(f"Erro na inicialização: {str(e)}")
    st.stop()

# Sidebar - Configurações
with st.sidebar:
    st.header("Configurações")
    
    openai_key = os.getenv("OPENAI_API_KEY", "")
    key_input = st.text_input(
        "Chave da OpenAI",
        type="password",
        value=openai_key,
        help="Insira sua chave da OpenAI (começa com 'sk-')"
    )
    openai_key = key_input or openai_key
    
    if openai_key:
        if openai_key.startswith('sk-'):
            st.success("✅ Chave válida detectada")
        else:
            st.error("❌ Formato inválido - deve começar com 'sk-'")
    else:
        st.warning("⚠️ Insira uma chave da OpenAI")

    st.markdown("""
    ### Exemplos de consultas:
    - "Liste os 5 estados com mais clientes"
    - "Mostre vendas por categoria como gráfico"
    - "Qual o ticket médio por canal?"
    """)

# Inicialização do LLM
try:
    if "llm" not in st.session_state and openai_key.startswith('sk-'):
        st.session_state.llm = OpenAI(
            openai_api_key=openai_key,
            temperature=0.3,
            max_tokens=1500,
            model="gpt-3.5-turbo-instruct"
        )
        st.session_state.agents = AgentsManager(st.session_state.llm, st.session_state.db)
except Exception as e:
    st.error(f"Erro ao inicializar IA: {str(e)}")

# Interface principal
user_input = st.text_area("Faça sua pergunta sobre os dados:", height=100)

if st.button("Analisar") and user_input:
    if not openai_key.startswith('sk-'):
        st.error("Configure uma chave válida da OpenAI")
        st.stop()
    
    if "agents" not in st.session_state:
        st.error("Sistema de IA não inicializado")
        st.stop()

    with st.spinner("Processando sua solicitação..."):
        try:
            # Container para resultados
            main_col, debug_col = st.columns([3, 1])
            
            with main_col:
                interpretation = st.session_state.agents.interpret_request(user_input)
                st.session_state.interpretation = interpretation
                
                sql_query = st.session_state.agents.generate_sql(interpretation)
                st.session_state.sql_query = sql_query
                
                results = st.session_state.db.execute_query(sql_query)
                st.session_state.results = results
                
                if not results.empty:
                    response = st.session_state.agents.format_response(
                        results.to_json(orient='records', force_ascii=False), 
                        user_input
                    )
                    st.markdown(response)
                    
                    chart_type = detect_chart_type(user_input)
                    if chart_type != "text":
                        fig = generate_visualization(results, chart_type)
                        if fig:
                            st.pyplot(fig)
                else:
                    st.warning("Nenhum resultado encontrado. Verifique:")
                    st.markdown("""
                    - Os filtros podem estar muito restritivos
                    - A tabela pode estar vazia
                    - Os nomes das colunas podem ser diferentes
                    """)
            
            with debug_col.expander("💻 Detalhes técnicos"):
                st.json(interpretation)
                st.code(sql_query, language="sql")
                st.dataframe(results.head(3) if not results.empty else pd.DataFrame())

        except Exception as e:
            st.error(f"Erro: {str(e)}")
            if "sql_query" in st.session_state:
                st.code(st.session_state.sql_query, language="sql")

# Rodapé
st.divider()
st.caption("Sistema de análise com IA v2.0 | Desenvolvido com Streamlit e LangChain")