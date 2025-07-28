# agents.py
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
import logging
import os
from pathlib import Path
import sqlite3

try:
    from .prompts import INTERPRETATION_PROMPT, SQL_PROMPT, FORMATTING_PROMPT, ERROR_PROMPT
except ImportError:
    # Fallback se não conseguir importar
    from langchain.prompts import PromptTemplate

    INTERPRETATION_PROMPT = PromptTemplate(
        input_variables=["user_input", "schema_info"],
        template="""
        Analise a solicitação considerando o schema do banco de dados disponível:

        Schema disponível: {schema_info}
        Solicitação: "{user_input}"

        Retorne apenas um JSON estruturado:
        {{
            "intencao": "descrição clara da análise solicitada",
            "tipo_analise": "ranking|distribuicao|tendencia|kpi|comparacao",
            "tabelas": ["lista de tabelas necessárias"],
            "metricas": ["métricas a serem calculadas"],
            "dimensoes": ["campos para agrupamento"],
            "filtros": ["condições de filtro se aplicável"],
            "limite": 10,
            "tipo_grafico": "barras|pizza|linha|tabela|scatter",
            "formato_saida": "completo"
        }}
        """
    )

    SQL_PROMPT = PromptTemplate(
        input_variables=["interpretation", "schema_info"],
        template="""
        Gere uma query SQL válida para SQLite baseada na interpretação e schema:

        Interpretação: {interpretation}

        Schema do banco:
        {schema_info}

        IMPORTANTE:
        - Use apenas as tabelas e colunas existentes no schema
        - Para datas, use DATE() ou strftime() do SQLite
        - Para JOINs, sempre use INNER JOIN com as chaves corretas
        - Limite resultados quando apropriado
        - Use agregações (COUNT, SUM, AVG) quando necessário

        Retorne APENAS a query SQL válida.
        """
    )


class DatabaseManager:
    """Gerenciador de conexão e operações com o banco de dados."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador do banco de dados.

        Args:
            db_path: Caminho para o banco de dados. Se None, usa o padrão.
        """
        self.db_path = self._get_db_path(db_path)
        self.logger = logging.getLogger(__name__)
        self._schema_cache = None

        # Verificar se o banco existe
        if not self.db_path.exists():
            self.logger.warning(
    f"Banco de dados não encontrado em: {
        self.db_path}")
            raise FileNotFoundError(
    f"Banco de dados não encontrado: {
        self.db_path}")

    def _get_db_path(self, db_path: Optional[str] = None) -> Path:
        """
        Determina o caminho do banco de dados usando caminhos relativos.

        Args:
            db_path: Caminho customizado (opcional)

        Returns:
            Path objeto com o caminho do banco
        """
        if db_path:
            return Path(db_path)

        # Usar caminho relativo padrão
        current_dir = Path(__file__).parent
        return current_dir / "data" / "clientes_completo.db"

    def get_connection(self) -> sqlite3.Connection:
        """
        Cria e retorna uma conexão com o banco de dados.

        Returns:
            Conexão SQLite
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            return conn
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    def execute_query(
    self,
    query: str,
     params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Executa uma query e retorna os resultados como DataFrame.

        Args:
            query: Query SQL
            params: Parâmetros para a query (opcional)

        Returns:
            DataFrame com os resultados
        """
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                self.logger.info(
    f"Query executada com sucesso. {
        len(df)} registros retornados.")
                return df
        except Exception as e:
            self.logger.error(f"Erro ao executar query: {e}")
            self.logger.error(f"Query: {query}")
            return pd.DataFrame()

    def get_schema(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        Obtém o schema do banco de dados (tabelas e colunas).

        Args:
            force_refresh: Force atualização do cache

        Returns:
            Dict com tabelas e suas colunas
        """
        if self._schema_cache is not None and not force_refresh:
            return self._schema_cache

        schema = {}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Obter lista de tabelas
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                # Para cada tabela, obter as colunas
                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    schema[table] = columns

                self._schema_cache = schema
                self.logger.info(f"Schema carregado: {list(schema.keys())}")

        except Exception as e:
            self.logger.error(f"Erro ao obter schema: {e}")
            # Fallback para schema padrão
            schema = {
    "clientes": [
        "id",
        "nome",
        "email",
        "idade",
        "cidade",
        "estado",
        "profissao",
        "genero"],
        "compras": [
            "id",
            "cliente_id",
            "data_compra",
            "valor",
            "categoria",
            "canal"],
            "suporte": [
                "id",
                "cliente_id",
                "data_contato",
                "tipo_contato",
                "resolvido",
                "canal"],
                "campanhas_marketing": [
                    "id",
                    "cliente_id",
                    "nome_campanha",
                    "data_envio",
                    "interagiu",
                     "canal"]}

        return schema

    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Valida uma query SQL sem executá-la.

        Args:
            query: Query SQL para validar

        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Usar EXPLAIN para validar sem executar
                cursor.execute(f"EXPLAIN {query}")
                return True, "Query válida"
        except Exception as e:
            return False, str(e)

    def get_table_sample(
    self,
    table_name: str,
     limit: int = 5) -> pd.DataFrame:
        """
        Obtém uma amostra de dados de uma tabela.

        Args:
            table_name: Nome da tabela
            limit: Número de registros

        Returns:
            DataFrame com amostra dos dados
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)


class AgentsManager:
    def __init__(
    self,
    llm,
    database_manager: Optional[DatabaseManager] = None,
     db_path: Optional[str] = None):
        """
        Inicializa o gerenciador de agentes com LLM e banco de dados.

        Args:
            llm: Modelo de linguagem (LangChain)
            database_manager: Instância do DatabaseManager (opcional)
            db_path: Caminho do banco de dados (usado se database_manager não fornecido)
        """
        self.llm = llm

        # Inicializar gerenciador do banco de dados
        if database_manager:
            self.db = database_manager
        else:
            self.db = DatabaseManager(db_path)

        self.logger = logging.getLogger(__name__)

        # Configurar estilo dos gráficos
        try:
            plt.style.use('seaborn-v0_8')
        except BaseException:
            plt.style.use('default')

        try:
            sns.set_palette("husl")
        except BaseException:
            pass


<< << << < HEAD
       # Schema do banco para referência
   self.schema = {
        "clientes": {
    "columns": [
        {"name": "id",
    "type": "INTEGER",
    "description": "Chave primária",
     "primary_key": True},
        {"name": "nome", "type": "TEXT", "description": "Nome completo do cliente"},
        {"name": "email", "type": "TEXT", "description": "E-mail único do cliente"},
        {"name": "idade", "type": "INTEGER", "description": "Idade em anos"},
        {"name": "cidade", "type": "TEXT", "description": "Cidade de residência"},
        {"name": "estado", "type": "TEXT",
            "description": "Sigla do estado (ex: SP, RJ)"},
        {"name": "profissao", "type": "TEXT", "description": "Profissão/ocupação"},
        {"name": "genero", "type": "TEXT", "description": "Identidade de gênero"}
    ],
    "description": "Tabela de cadastro de clientes",
    "foreign_keys": []
},
        "compras": {
    "columns": [
        {"name": "id",
    "type": "INTEGER",
    "description": "Chave primária",
     "primary_key": True},
        {"name": "cliente_id",
    "type": "INTEGER",
    "description": "Chave estrangeira para clientes",
     "foreign_key": "clientes.id"},
        {"name": "data_compra", "type": "TEXT",
            "description": "Data no formato ISO (YYYY-MM-DD)"},
        {"name": "valor", "type": "REAL", "description": "Valor total da compra"},
        {"name": "categoria", "type": "TEXT",
            "description": "Categoria do produto/serviço"},
        {"name": "canal", "type": "TEXT",
            "description": "Canal de venda (online/loja/telefone)"}
    ],
    "description": "Registro de transações de compras",
    "foreign_keys": ["cliente_id"]
},
        "suporte": {
    "columns": [
        {"name": "id",
    "type": "INTEGER",
    "description": "Chave primária",
     "primary_key": True},
        {"name": "cliente_id",
    "type": "INTEGER",
    "description": "Chave estrangeira para clientes",
     "foreign_key": "clientes.id"},
        {"name": "data_contato", "type": "TEXT",
            "description": "Data no formato ISO (YYYY-MM-DD)"},
        {"name": "tipo_contato", "type": "TEXT",
            "description": "Tipo de solicitação (reclamação/duvida/elogio)"},
        {"name": "resolvido", "type": "BOOLEAN",
            "description": "Indica se o ticket foi resolvido (0/1)"},
        {"name": "canal", "type": "TEXT",
            "description": "Canal de atendimento (email/telefone/chat)"}
    ],
    "description": "Registro de atendimentos ao cliente",
    "foreign_keys": ["cliente_id"]
},
        "campanhas_marketing": {
    "columns": [
        {"name": "id",
    "type": "INTEGER",
    "description": "Chave primária",
     "primary_key": True},
        {"name": "cliente_id",
    "type": "INTEGER",
    "description": "Chave estrangeira para clientes",
     "foreign_key": "clientes.id"},
        {"name": "nome_campanha", "type": "TEXT",
            "description": "Nome/identificador da campanha"},
        {"name": "data_envio", "type": "TEXT",
            "description": "Data no formato ISO (YYYY-MM-DD)"},
        {"name": "interagiu", "type": "BOOLEAN",
            "description": "Se o cliente interagiu com a campanha (0/1)"},
        {"name": "canal", "type": "TEXT",
            "description": "Canal de marketing (email/sms/push/whatsapp)"}
    ],
    "description": "Registro de campanhas de marketing enviadas",
    "foreign_keys": ["cliente_id"]
},
        "metadata": {
    "database_type": "SQLite",
    "date_format": "ISO 8601 (YYYY-MM-DD)",
    "version": "1.0",
    "description": "Esquema para sistema de CRM e vendas"
}
        }
== == == =
   # Obter schema dinâmico do banco
   self.schema = self.db.get_schema()
    self.logger.info(
    f"AgentsManager inicializado com tabelas: {
        list(
            self.schema.keys())}")
>>>>>> > dab40b277b91c7dfd8ab814e069056bf0ee0e959

   def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """
        Interpreta a solicitação do usuário e determina o tipo de análise.

        Args:
            user_input: Pergunta do usuário

        Returns:
            Dict com interpretação estruturada
        """
        try:
            # Preparar informações do schema para o LLM
            schema_info = self._format_schema_for_llm()

            # Usar o prompt template com schema
            prompt = INTERPRETATION_PROMPT.format(
                user_input=user_input,
                schema_info=schema_info
            )
            response = self.llm(prompt)

            # Limpar e parsear resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                interpretation = json.loads(json_match.group())
                # Validar se as tabelas existem
                interpretation = self._validate_interpretation(interpretation)
            else:
                # Fallback para interpretação básica
                interpretation = self._fallback_interpretation(user_input)

            self.logger.info(f"Interpretação gerada: {interpretation}")
            return interpretation

        except Exception as e:
            self.logger.error(f"Erro na interpretação: {e}")
            return self._fallback_interpretation(user_input)

    def _format_schema_for_llm(self) -> str:
        """Formata o schema do banco para uso no prompt do LLM."""
        schema_lines = []
        for table, columns in self.schema.items():
            columns_str = ", ".join(columns)
            schema_lines.append(f"- {table}({columns_str})")
        return "\n".join(schema_lines)

    def _validate_interpretation(
        self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e corrige a interpretação baseada no schema real."""
        # Verificar se as tabelas existem
        valid_tables = []
        for table in interpretation.get("tabelas", []):
            if table in self.schema:
                valid_tables.append(table)
            else:
                self.logger.warning(f"Tabela '{table}' não existe no schema")

        if not valid_tables:
            # Se nenhuma tabela válida, usar a primeira disponível
            valid_tables = [list(self.schema.keys())[0]]

        interpretation["tabelas"] = valid_tables
        return interpretation

    def _fallback_interpretation(self, user_input: str) -> Dict[str, Any]:
        """Interpretação básica quando o LLM falha."""
        user_lower = user_input.lower()

        # Determinar tipo de gráfico
        if any(
    word in user_lower for word in [
        'ranking',
        'top',
        'maior',
         'menor']):
            tipo_grafico = "barras"
            tipo_analise = "ranking"
        elif any(word in user_lower for word in ['distribuição', 'participação', '%']):
            tipo_grafico = "pizza"
            tipo_analise = "distribuicao"
        elif any(word in user_lower for word in ['tendência', 'evolução', 'tempo']):
            tipo_grafico = "linha"
            tipo_analise = "tendencia"
        else:
            tipo_grafico = "tabela"
            tipo_analise = "kpi"

        # Usar tabelas que realmente existem
        available_tables = list(self.schema.keys())
        default_tables = []

        if "clientes" in available_tables:
            default_tables.append("clientes")
        if "compras" in available_tables:
            default_tables.append("compras")

        if not default_tables:
            default_tables = [available_tables[0]]

        return {
            "intencao": f"Análise baseada em: {user_input}",
            "tipo_analise": tipo_analise,
            "tabelas": default_tables,
            "metricas": ["COUNT(*)", "SUM(valor)" if "compras" in default_tables else "COUNT(*)"],
            "dimensoes": ["estado" if "clientes" in default_tables else list(self.schema[default_tables[0]])[1]],
            "filtros": [],
            "limite": 10,
            "tipo_grafico": tipo_grafico,
            "formato_saida": "completo"
        }

    def generate_sql(self, interpretation: Dict[str, Any]) -> str:
        """
        Gera query SQL baseada na interpretação.

        Args:
            interpretation: Dicionário com a interpretação

        Returns:
            String SQL válida
        """
        try:
            # Preparar informações do schema
            schema_info = self._format_schema_for_llm()

            # Usar o prompt template
            prompt = SQL_PROMPT.format(
                interpretation=json.dumps(interpretation, indent=2),
                schema_info=schema_info
            )
            response = self.llm(prompt)

            # Limpar resposta
            sql_query = re.sub(
                r'^```sql\s*|\s*```$',
                '',
                response.strip(),
                flags=re.MULTILINE)
            sql_query = sql_query.strip()

            # Validar query
            is_valid, error_msg = self.db.validate_query(sql_query)
            if not is_valid:
                self.logger.error(f"Query inválida: {error_msg}")
                # Tentar uma query básica como fallback
                first_table = list(self.schema.keys())[0]
                sql_query = f"SELECT * FROM {first_table} LIMIT 10"

            self.logger.info(f"Query SQL gerada: {sql_query}")
            return sql_query

        except Exception as e:
            self.logger.error(f"Erro na geração SQL: {e}")
            # Fallback para query básica
            first_table = list(self.schema.keys())[0]
            return f"SELECT * FROM {first_table} LIMIT 10"

    def execute_analysis(self, user_input: str) -> Dict[str, Any]:
        """
        Executa análise completa: interpretação, geração SQL, execução e formatação.

        Args:
            user_input: Pergunta do usuário

        Returns:
            Dict com resultado completo da análise
        """
        try:
            # 1. Interpretar solicitação
            interpretation = self.interpret_request(user_input)

            # 2. Gerar SQL
            sql_query = self.generate_sql(interpretation)

            # 3. Executar query
            df = self.db.execute_query(sql_query)

            # 4. Formatar resposta completa
            response = self.format_complete_response(
                df, interpretation, user_input)
            response["sql_query"] = sql_query

            return response

        except Exception as e:
            self.logger.error(f"Erro na análise completa: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": f"❌ **Erro na análise**: {str(e)}",
                "data": pd.DataFrame(),
                "sql_query": "",
                "interpretation": {}
            }

    def format_response(self, query_results_json: str, user_input: str) -> str:
        """
        Método de compatibilidade com código antigo.
        Formata resposta em texto simples.
        """
        try:
            # Converter JSON para DataFrame
            if isinstance(query_results_json, str):
                data = json.loads(query_results_json)
                df = pd.DataFrame(data)
            else:
                df = query_results_json

            if df.empty:
                return "❌ **Nenhum resultado encontrado** para sua consulta."

            # Gerar resumo básico
            total_rows = len(df)
            summary = f"📊 **Análise concluída**: {total_rows} registros encontrados.\n\n"

            # Adicionar informações sobre colunas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                for col in numeric_cols[:2]:  # Máximo 2 colunas
                    total = df[col].sum()
                    media = df[col].mean()
                    summary += f"**{col.replace('_',
     ' ').title()}**: Total {total:,.2f} | Média {media:,.2f}\n"

            return summary

        except Exception as e:
            self.logger.error(f"Erro na formatação: {e}")
            return "⚠️ **Dados processados com sucesso**, mas houve erro na formatação."

    def create_visualizations(self,
    df: pd.DataFrame,
    interpretation: Dict[str,
    Any]) -> Tuple[Optional[Any],
     Optional[Any]]:
        """
        Cria visualizações matplotlib e plotly baseadas nos dados.

        Args:
            df: DataFrame com os dados
            interpretation: Interpretação da solicitação

        Returns:
            Tuple[matplotlib.figure, plotly.figure]
        """
        if df.empty:
            return None, None

        try:
            tipo_grafico = interpretation.get("tipo_grafico", "barras")

            # Preparar dados
            x_col = df.columns[0]
            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

            # Matplotlib Figure
            fig_mpl, ax = plt.subplots(figsize=(12, 8))

            # Plotly Figure
            fig_plotly = None

            if tipo_grafico == "barras":
                fig_mpl, fig_plotly = self._create_bar_charts(
                    df, x_col, y_col, ax)
            elif tipo_grafico == "pizza":
                fig_mpl, fig_plotly = self._create_pie_charts(
                    df, x_col, y_col, ax)
            elif tipo_grafico == "linha":
                fig_mpl, fig_plotly = self._create_line_charts(
                    df, x_col, y_col, ax)
            elif tipo_grafico == "scatter":
                fig_mpl, fig_plotly = self._create_scatter_charts(
                    df, x_col, y_col, ax)
            else:
                # Default para barras
                fig_mpl, fig_plotly = self._create_bar_charts(
                    df, x_col, y_col, ax)

            # Configurações gerais matplotlib
            plt.title(
                interpretation.get("intencao", "Análise de Dados"),
                fontsize=16,
                fontweight='bold'
            )
            plt.tight_layout()

            return fig_mpl, fig_plotly

        except Exception as e:
            self.logger.error(f"Erro na criação de visualizações: {e}")
            return None, None

    def _create_bar_charts(self, df: pd.DataFrame,
                           x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de barras matplotlib e plotly."""
        try:
            # Matplotlib
            colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
            bars = ax.bar(df[x_col], df[y_col], color=colors)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())

            # Adicionar valores nas barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height:,.0f}', ha='center', va='bottom')

            # Rotacionar labels se necessário
            if len(df) > 5:
                plt.xticks(rotation=45, ha='right')

            # Plotly
            fig_plotly = px.bar(
                df, x=x_col, y=y_col,
                title=f"{y_col.replace('_', ' ').title()} por {x_col.replace('_', ' ').title()}"
            )
            fig_plotly.update_traces(
    texttemplate='%{y:,.0f}',
     textposition='outside')

            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de barras: {e}")
            return plt.gcf(), None

    def _create_pie_charts(self, df: pd.DataFrame,
                           x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de pizza matplotlib e plotly."""
        try:
            # Matplotlib
            colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
            wedges, texts, autotexts = ax.pie(
                df[y_col], labels=df[x_col], autopct='%1.1f%%',
                colors=colors
            )
            ax.axis('equal')

            # Plotly
            fig_plotly = px.pie(
                df, values=y_col, names=x_col,
                title=f"Distribuição de {y_col.replace('_', ' ').title()}"
            )
            fig_plotly.update_traces(
    textposition='inside',
     textinfo='percent+label')

            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de pizza: {e}")
            return plt.gcf(), None

    def _create_line_charts(self, df: pd.DataFrame,
                            x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de linha matplotlib e plotly."""
        try:
            # Matplotlib
            ax.plot(
    df[x_col],
    df[y_col],
    marker='o',
    linewidth=2,
     markersize=6)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.grid(True, alpha=0.3)

            # Plotly
            fig_plotly = px.line(
                df, x=x_col, y=y_col,
                title=f"Tendência de {y_col.replace('_', ' ').title()}",
                markers=True
            )
            fig_plotly.update_traces(line=dict(width=3), marker=dict(size=8))

            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de linha: {e}")
            return plt.gcf(), None

    def _create_scatter_charts(
        self, df: pd.DataFrame, x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de dispersão matplotlib e plotly."""
        try:
            # Matplotlib
            ax.scatter(df[x_col], df[y_col], alpha=0.6, s=60)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.grid(True, alpha=0.3)

            # Plotly
            fig_plotly = px.scatter(
    df, x=x_col, y=y_col, title=f"Correlação: {
        x_col.replace(
            '_', ' ').title()} vs {
                y_col.replace(
                    '_', ' ').title()}" )

            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de dispersão: {e}")
            return plt.gcf(), None

    def generate_summary(self, df: pd.DataFrame,
                         interpretation: Dict[str, Any]) -> str:
        """
        Gera resumo textual inteligente dos dados.

        Args:
            df: DataFrame com os resultados
            interpretation: Interpretação da solicitação

        Returns:
            String com resumo formatado
        """
        if df.empty:
            return "❌ **Nenhum dado encontrado** para a análise solicitada."

        try:
            # Análise estatística básica
            total_rows = len(df)
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            summary_parts = []

            # Cabeçalho
            summary_parts.append(
                f"📊 **Resumo da Análise**: {interpretation.get('intencao', 'Análise de dados')}")
            summary_parts.append(f"📈 **Total de registros**: {total_rows:,}")

            # Análise por tipo
            tipo_analise = interpretation.get("tipo_analise", "kpi")

            if tipo_analise == "ranking" and len(numeric_cols) > 0:
                valor_col = numeric_cols[0]
                categoria_col = df.columns[0]

                # Top performer
                top_1 = df.iloc[0]
                summary_parts.append(
                    f"🥇 **Líder**: {top_1[categoria_col]} com {top_1[valor_col]:,.2f}")

                # Estatísticas
                total = df[valor_col].sum()
                media = df[valor_col].mean()
                summary_parts.append(f"💰 **Total geral**: {total:,.2f}")
                summary_parts.append(f"📊 **Média**: {media:,.2f}")

            elif len(numeric_cols) > 0:
                # Análise geral
                for col in numeric_cols[:2]:  # Máximo 2 colunas numéricas
                    total = df[col].sum()
                    media = df[col].mean()
                    summary_parts.append(
                        f"📊 **{col.replace('_', ' ').title()}**: Total {total:,.2f} | Média {media:,.2f}")

            return "\n\n".join(summary_parts)

        except Exception as e:
            self.logger.error(f"Erro na geração do resumo: {e}")
            return f"⚠️ **Dados obtidos**: {
    len(df)} registros. Resumo detalhado indisponível."

    def format_complete_response(self,
    df: pd.DataFrame,
    interpretation: Dict[str,
    Any],
    user_input: str) -> Dict[str,
     Any]:
        """
        Formata resposta completa com tabela, resumo e gráficos.

        Args:
            df: DataFrame com os dados
            interpretation: Interpretação da solicitação
            user_input: Pergunta original do usuário

        Returns:
            Dict com todos os componentes da resposta
        """
        response = {
            "success": not df.empty,
            "data": df,
            "summary": "",
            "table_html": "",
            "matplotlib_fig": None,
            "plotly_fig": None,
            "interpretation": interpretation,
            "total_records": len(df)
        }

        if df.empty:
            response["summary"] = "❌ **Nenhum resultado encontrado** para sua consulta."
            return response

        try:
            # Gerar resumo textual
            response["summary"] = self.generate_summary(df, interpretation)

            # Formatar tabela HTML
            response["table_html"] = self._format_table_html(df)

            # Criar visualizações
            mpl_fig, plotly_fig = self.create_visualizations(
                df, interpretation)
            response["matplotlib_fig"] = mpl_fig
            response["plotly_fig"] = plotly_fig

            self.logger.info(
    f"Resposta completa gerada com {
        len(df)} registros")

        except Exception as e:
            self.logger.error(f"Erro na formatação da resposta: {e}")
            response["summary"] = f"⚠️ **Dados obtidos**: {
    len(df)} registros. Erro na formatação: {
        str(e)}"

        return response

    def _format_table_html(self, df: pd.DataFrame) -> str:
        """Formata DataFrame como HTML table responsiva."""
        try:
            # Limitar a 20 linhas para exibição
            display_df = df.head(20)

            # Formatação especial para colunas numéricas
            formatted_df = display_df.copy()

            for col in formatted_df.select_dtypes(include=[np.number]).columns:
                if 'valor' in col.lower() or 'preco' in col.lower():
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"R$ {x:,.2f}")
                else:
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{x:,.0f}")

            # Gerar HTML com estilo
            html = formatted_df.to_html(
                index=False,
                classes='table table-striped table-hover',
                table_id='results-table',
                escape=False
            )

            # Adicionar indicador se há mais dados
            if len(df) > 20:
                html += f"<p><small><i>Mostrando 20 de {
    len(df)} registros totais</i></small></p>"

            return html

        except Exception as e:
            self.logger.error(f"Erro na formatação da tabela: {e}")
            return df.head(10).to_html(index=False)

    def get_database_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o banco de dados.

        Returns:
            Dict com informações do banco
        """
        try:
            info = {
                "database_path": str(self.db.db_path),
                "database_exists": self.db.db_path.exists(),
                "schema": self.schema,
                "table_count": len(self.schema),
                "tables": list(self.schema.keys())
            }

            # Adicionar contagem de registros por tabela
            table_counts = {}
            for table in self.schema.keys():
                try:
                    count_df = self.db.execute_query(
    f"SELECT COUNT(*) as count FROM {table}")
                    table_counts[table] = count_df.iloc[0]['count'] if not count_df.empty else 0
                except Exception as e:
                    self.logger.warning(
    f"Erro ao contar registros da tabela {table}: {e}")
                    table_counts[table] = "N/A"

            info["table_record_counts"] = table_counts
            return info

        except Exception as e:
            self.logger.error(f"Erro ao obter informações do banco: {e}")
            return {
    "error": str(e),
    "database_path": str(
        self.db.db_path) if hasattr(
            self,
            'db') else "N/A",
             "database_exists": False }

    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com o banco de dados.

        Returns:
            Dict com resultado do teste
        """
        try:
            # Testar conexão básica
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            # Testar algumas queries básicas
            schema = self.db.get_schema()
            first_table = list(schema.keys())[0]
            sample_data = self.db.get_table_sample(first_table, 1)

            return {
    "success": True,
    "message": "Conexão com banco de dados estabelecida com sucesso",
    "database_path": str(
        self.db.db_path),
        "tables_available": list(
            schema.keys()),
            "sample_query_successful": not sample_data.empty,
             "total_tables": len(schema) }

        except Exception as e:
            self.logger.error(f"Erro no teste de conexão: {e}")
            return {
    "success": False,
    "error": str(e),
    "message": "Falha na conexão com o banco de dados",
    "database_path": str(
        self.db.db_path) if hasattr(
            self,
             'db') else "N/A" }

    def refresh_schema(self):
        """Força atualização do schema do banco de dados."""
        try:
            self.schema = self.db.get_schema(force_refresh=True)
            self.logger.info(f"Schema atualizado: {list(self.schema.keys())}")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar schema: {e}")

# Função utilitária para criar instância com configuração padrão

def create_agents_manager(llm, db_path: Optional[str] = None) -> AgentsManager:
    """
    Cria uma instância do AgentsManager com configuração padrão.

    Args:
        llm: Modelo de linguagem
        db_path: Caminho customizado para o banco (opcional)

    Returns:
        Instância configurada do AgentsManager
    """
    try:
        # Configurar logging se não estiver configurado
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Criar gerenciador
        agents_manager = AgentsManager(llm, db_path=db_path)

        # Testar conexão
        test_result = agents_manager.test_connection()
        if test_result["success"]:
            print(f"✅ AgentsManager criado com sucesso!")
            print(f"📁 Banco: {test_result['database_path']}")
            print(f"📊 Tabelas: {', '.join(test_result['tables_available'])}")
        else:
            print(f"❌ Erro na inicialização: {test_result['error']}")

        return agents_manager

    except Exception as e:
        print(f"❌ Erro ao criar AgentsManager: {e}")
        raise


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de como usar o AgentsManager

    # Simulação de LLM para teste (substitua por seu LLM real)
    class MockLLM:
        def __call__(self, prompt):
            # Simulação básica - substitua por seu LLM real
            if "interpretação" in prompt.lower():
                return '''
                {
                    "intencao": "Análise de teste",
                    "tipo_analise": "ranking",
                    "tabelas": ["clientes"],
                    "metricas": ["COUNT(*)"],
                    "dimensoes": ["estado"],
                    "filtros": [],
                    "limite": 10,
                    "tipo_grafico": "barras",
                    "formato_saida": "completo"
                }
                '''
            else:
                return "SELECT estado, COUNT(*) as total FROM clientes GROUP BY estado ORDER BY total DESC LIMIT 10"

    try:
        # Criar instância de teste
        mock_llm = MockLLM()
        agents = create_agents_manager(mock_llm)

        # Testar funcionalidades
        print("\n🔍 Informações do banco:")
        db_info = agents.get_database_info()
        for key, value in db_info.items():
            print(f"  {key}: {value}")

        # Exemplo de análise
        print("\n📊 Executando análise de exemplo...")
        result = agents.execute_analysis(
            "Mostre o ranking de clientes por estado")
        print(
    f"✅ Análise concluída: {
        result['total_records']} registros encontrados")

    except Exception as e:
        print(f"❌ Erro no exemplo: {e}")
        print("💡 Certifique-se de que o banco 'data/clientes_completo.db' existe")
