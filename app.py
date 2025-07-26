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
import sqlite3

# Configuração de caminhos
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

# Configuração inicial
load_dotenv()
st.set_page_config(page_title="Analytics com IA", layout="wide")
st.title("📊 Analytics com IA")

# Verificação do banco de dados
DB_PATH = PROJECT_ROOT / 'data' / 'clientes_completo.db'

# DIAGNÓSTICO DETALHADO DO BANCO
def diagnose_database():
    st.header("🔧 Diagnóstico Completo do Banco de Dados")
    
    # 1. Verificar se o arquivo existe
    st.subheader("1. Verificação do Arquivo")
    if DB_PATH.exists():
        st.success(f"✅ Arquivo encontrado: {DB_PATH}")
        file_size = DB_PATH.stat().st_size
        st.info(f"Tamanho do arquivo: {file_size:,} bytes")
        
        if file_size == 0:
            st.error("❌ PROBLEMA: Arquivo está vazio!")
            return False
    else:
        st.error(f"❌ Arquivo não encontrado em: {DB_PATH}")
        
        # Listar arquivos no diretório data
        data_dir = PROJECT_ROOT / 'data'
        if data_dir.exists():
            st.info("Arquivos encontrados no diretório 'data':")
            for file in data_dir.iterdir():
                st.write(f"- {file.name} ({file.stat().st_size:,} bytes)")
        else:
            st.error("Diretório 'data' não existe!")
        return False
    
    # 2. Testar conexão direta com SQLite
    st.subheader("2. Teste de Conexão Direta")
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            st.success(f"✅ Conexão estabelecida! Encontradas {len(tables)} tabelas:")
            for table in tables:
                st.write(f"- {table[0]}")
        else:
            st.error("❌ Nenhuma tabela encontrada no banco!")
            conn.close()
            return False
        
        # 3. Verificar conteúdo de cada tabela
        st.subheader("3. Verificação do Conteúdo das Tabelas")
        for table in tables:
            table_name = table[0]
            st.write(f"**Tabela: {table_name}**")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            st.write(f"Registros: {count:,}")
            
            if count > 0:
                # Mostrar estrutura da tabela
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                st.write("Colunas:")
                for col in columns:
                    st.write(f"  - {col[1]} ({col[2]})")
                
                # Mostrar alguns dados
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                if sample_data:
                    df_sample = pd.DataFrame(sample_data, columns=[col[1] for col in columns])
                    st.dataframe(df_sample)
            else:
                st.warning(f"⚠️ Tabela {table_name} está vazia!")
            
            st.divider()
        
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Erro na conexão direta: {str(e)}")
        return False

# 4. Testar DatabaseManager
def test_database_manager():
    st.subheader("4. Teste do DatabaseManager")
    try:
        db = DatabaseManager(str(DB_PATH))
        if db.connect():
            st.success("✅ DatabaseManager conectou com sucesso!")
            
            # Testar queries básicas
            test_queries = {
                "Clientes": "SELECT COUNT(*) as total FROM clientes",
                "Compras": "SELECT COUNT(*) as total FROM compras", 
                "Suporte": "SELECT COUNT(*) as total FROM suporte",
                "Campanhas": "SELECT COUNT(*) as total FROM campanhas_marketing"
            }
            
            for nome, query in test_queries.items():
                try:
                    df = db.execute_query(query)
                    if not df.empty:
                        total = df.iloc[0, 0]
                        st.success(f"✅ {nome}: {total:,} registros")
                    else:
                        st.error(f"❌ {nome}: Query retornou vazio")
                except Exception as e:
                    st.error(f"❌ {nome}: Erro na query - {str(e)}")
            
            return db
        else:
            st.error("❌ DatabaseManager falhou ao conectar!")
            return None
            
    except Exception as e:
        st.error(f"❌ Erro no DatabaseManager: {str(e)}")
        return None

# EXECUTAR DIAGNÓSTICO
if st.button("🔍 Executar Diagnóstico Completo"):
    with st.spinner("Diagnosticando banco de dados..."):
        db_ok = diagnose_database()
        
        if db_ok:
            test_db = test_database_manager()
            if test_db:
                st.session_state.db = test_db
                st.success("🎉 Banco de dados funcionando corretamente!")
            else:
                st.error("❌ Problema no DatabaseManager")
        else:
            st.error("❌ Problemas no banco de dados detectados")

# RESTO DO CÓDIGO ORIGINAL (apenas se o diagnóstico passou)
if "db" in st.session_state:
    
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

else:
    st.warning("⚠️ Execute o diagnóstico primeiro para verificar o banco de dados!")

# Rodapé
st.divider()
st.caption("Sistema de análise com IA v2.0 | Desenvolvido com Streamlit e LangChain")