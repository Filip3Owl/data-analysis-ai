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


class AgentsManager:
    def __init__(self, llm, database_manager):
        """
        Inicializa o gerenciador de agentes com LLM e banco de dados.

        Args:
            llm: Modelo de linguagem (LangChain)
            database_manager: Instância do DatabaseManager
        """
        self.llm = llm
        self.db = database_manager
        self.logger = logging.getLogger(__name__)

        # Configurar estilo dos gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Schema do banco para referência
        self.schema = {
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

    def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """
        Interpreta a solicitação do usuário e determina o tipo de análise.

        Args:
            user_input: Pergunta do usuário

        Returns:
            Dict com interpretação estruturada
        """
        try:
            # Prompt melhorado para interpretação
            interpretation_prompt = f"""
            Analise esta solicitação e retorne um JSON estruturado:

            Solicitação: "{user_input}"

            Schema disponível:
            - clientes: id, nome, email, idade, cidade, estado, profissao, genero
            - compras: id, cliente_id, data_compra, valor, categoria, canal
            - suporte: id, cliente_id, data_contato, tipo_contato, resolvido, canal
            - campanhas_marketing: id, cliente_id, nome_campanha, data_envio, interagiu, canal

            Retorne APENAS este JSON:
            {{
                "intencao": "descrição clara",
                "tipo_analise": "ranking|distribuicao|tendencia|comparacao|kpi",
                "tabelas": ["lista de tabelas necessárias"],
                "metricas": ["métricas a calcular"],
                "dimensoes": ["campos para agrupamento"],
                "filtros": ["condições WHERE"],
                "limite": 10,
                "tipo_grafico": "barras|pizza|linha|scatter|heatmap|tabela",
                "formato_saida": "completo"
            }}
            """

            response = self.llm(interpretation_prompt)

            # Limpar e parsear resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                interpretation = json.loads(json_match.group())
            else:
                # Fallback para interpretação básica
                interpretation = self._fallback_interpretation(user_input)

            self.logger.info(f"Interpretação gerada: {interpretation}")
            return interpretation

        except Exception as e:
            self.logger.error(f"Erro na interpretação: {e}")
            return self._fallback_interpretation(user_input)

    def _fallback_interpretation(self, user_input: str) -> Dict[str, Any]:
        """Interpretação básica quando o LLM falha."""
        # Análise simples baseada em palavras-chave
        user_lower = user_input.lower()

        # Determinar tipo de gráfico
        if any(word in user_lower for word in ['ranking', 'top', 'maior', 'menor']):
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

        return {
            "intencao": f"Análise baseada em: {user_input}",
            "tipo_analise": tipo_analise,
            "tabelas": ["clientes", "compras"],
            "metricas": ["COUNT(*)", "SUM(valor)"],
            "dimensoes": ["estado"],
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
            sql_prompt = f"""
            Gere uma query SQL válida para SQLite baseada nesta interpretação:

            {json.dumps(interpretation, indent=2)}

            Schema:
            - clientes(id, nome, email, idade, cidade, estado, profissao, genero)
            - compras(id, cliente_id, data_compra, valor, categoria, canal)
            - suporte(id, cliente_id, data_contato, tipo_contato, resolvido, canal)
            - campanhas_marketing(id, cliente_id, nome_campanha, data_envio, interagiu, canal)

            Regras:
            1. Use JOINs quando necessário
            2. Formate valores monetários com ROUND(valor, 2)
            3. Use aliases descritivos
            4. Inclua ORDER BY e LIMIT quando apropriado
            5. Para datas use strftime para formatação

            Retorne APENAS a query SQL:
            """

            response = self.llm(sql_prompt)

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
                raise ValueError(f"Query SQL inválida: {error_msg}")

            self.logger.info(f"Query SQL gerada: {sql_query}")
            return sql_query

        except Exception as e:
            self.logger.error(f"Erro na geração SQL: {e}")
            raise

    def _validate_data_for_chart(self, df: pd.DataFrame,
                                 chart_type: str) -> Tuple[bool, str, str]:
        """
        Valida se os dados são adequados para o tipo de gráfico.

        Args:
            df: DataFrame com os dados
            chart_type: Tipo do gráfico

        Returns:
            Tuple[is_valid, x_column, y_column]
        """
        if df.empty:
            return False, "", ""

        # Identificar colunas adequadas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=['object', 'category']).columns.tolist()

        # Para gráficos de barras e pizza: precisa de pelo menos 1 categórica e 1 numérica
        if chart_type in ["barras", "pizza"]:
            if len(numeric_cols) == 0:
                # Se não há colunas numéricas, criar uma contagem
                if len(categorical_cols) > 0:
                    x_col = categorical_cols[0]
                    # Criar coluna de contagem
                    df_grouped = df.groupby(x_col).size().reset_index(name='count')
                    return True, x_col, 'count'
                else:
                    return False, "", ""
            else:
                x_col = categorical_cols[0] if categorical_cols else df.columns[0]
                y_col = numeric_cols[0]
                return True, x_col, y_col

        # Para gráficos de linha: idealmente precisa de dados ordenáveis
        elif chart_type == "linha":
            if len(numeric_cols) >= 2:
                return True, df.columns[0], numeric_cols[0]
            elif len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                return True, categorical_cols[0], numeric_cols[0]
            else:
                return True, df.columns[0], df.columns[1] if len(
                    df.columns) > 1 else df.columns[0]

        # Para scatter: precisa de 2 colunas numéricas
        elif chart_type == "scatter":
            if len(numeric_cols) >= 2:
                return True, numeric_cols[0], numeric_cols[1]
            else:
                # Fallback para barras
                return self._validate_data_for_chart(df, "barras")

        # Default
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        return True, x_col, y_col

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

            # Validar e preparar dados
            is_valid, x_col, y_col = self._validate_data_for_chart(
                df.copy(), tipo_grafico)

            if not is_valid:
                self.logger.warning("Dados não adequados para visualização")
                return None, None

            # Se precisamos agrupar dados para contagem
            if y_col == 'count' and 'count' not in df.columns:
                df_plot = df.groupby(x_col).size().reset_index(name='count')
            else:
                df_plot = df.copy()

            # Limitar dados para visualização (máximo 20 categorias)
            if len(df_plot) > 20:
                df_plot = df_plot.head(20)
                self.logger.info(f"Dados limitados a 20 registros para visualização")

            # Matplotlib Figure
            fig_mpl, ax = plt.subplots(figsize=(12, 8))

            # Plotly Figure
            fig_plotly = None

            if tipo_grafico == "barras":
                fig_mpl, fig_plotly = self._create_bar_charts(df_plot, x_col, y_col, ax)
            elif tipo_grafico == "pizza":
                fig_mpl, fig_plotly = self._create_pie_charts(df_plot, x_col, y_col, ax)
            elif tipo_grafico == "linha":
                fig_mpl, fig_plotly = self._create_line_charts(
                    df_plot, x_col, y_col, ax)
            elif tipo_grafico == "scatter":
                fig_mpl, fig_plotly = self._create_scatter_charts(
                    df_plot, x_col, y_col, ax)
            else:
                # Default para barras
                fig_mpl, fig_plotly = self._create_bar_charts(df_plot, x_col, y_col, ax)

            # Configurações gerais matplotlib
            plt.title(
                interpretation.get(
                    "intencao",
                    "Análise de Dados"),
                fontsize=16,
                fontweight='bold')
            plt.tight_layout()

            return fig_mpl, fig_plotly

        except Exception as e:
            self.logger.error(f"Erro na criação de visualizações: {e}")
            # Tentar criar um gráfico simples como fallback
            try:
                return self._create_fallback_chart(df)
            except BaseException:
                return None, None

    def _create_fallback_chart(
            self, df: pd.DataFrame) -> Tuple[Optional[Any], Optional[Any]]:
        """Cria gráfico simples como fallback."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Apenas mostrar os primeiros valores como texto
            ax.text(0.5, 0.5, f"Dados disponíveis:\n{len(df)} registros",
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            return fig, None
        except BaseException:
            return None, None

    def _create_bar_charts(self, df: pd.DataFrame, x_col: str,
                           y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de barras matplotlib e plotly."""
        try:
            # Garantir que temos dados válidos
            if y_col != 'count':  # Não converter coluna de contagem
                if df[y_col].dtype not in [np.number]:
                    # Tentar converter para numérico
                    try:
                        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                        df = df.dropna(subset=[y_col])
                    except Exception as e:
                        self.logger.warning(f"Não foi possível converter {y_col} para numérico: {e}")
                        # Se não puder converter, usar contagem
                        df = df.groupby(x_col).size().reset_index(name='count')
                        y_col = 'count'

            if df.empty:
                raise ValueError("Nenhum dado numérico válido após conversão")

            # Matplotlib - Usar range() para posições das barras
            x_positions = range(len(df))
            bars = ax.bar(
                x_positions,
                df[y_col],
                color=sns.color_palette(
                    "husl",
                    len(df)))

            # Configurar labels do eixo x
            ax.set_xticks(x_positions)
            ax.set_xticklabels(df[x_col].astype(str), rotation=45, ha='right')
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())

            # Adicionar valores nas barras
            for i, (pos, value) in enumerate(zip(x_positions, df[y_col])):
                ax.text(pos, value, f'{value:,.0f}', ha='center', va='bottom')

            # Plotly
            fig_plotly = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=f"{
                    y_col.replace(
                        '_',
                        ' ').title()} por {
                    x_col.replace(
                        '_',
                        ' ').title()}",
                color=y_col if y_col != 'count' else None,
                color_continuous_scale="viridis" if y_col != 'count' else None)
            fig_plotly.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
            fig_plotly.update_layout(showlegend=False)

            return plt.gcf(), fig_plotly

        except Exception as e:
            self.logger.error(f"Erro na criação de gráfico de barras: {e}")
            raise

    def _create_pie_charts(self, df: pd.DataFrame, x_col: str,
                           y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de pizza matplotlib e plotly."""
        try:
            # Garantir que temos dados válidos
            if y_col != 'count':  # Não converter coluna de contagem
                if df[y_col].dtype not in [np.number]:
                    # Tentar converter para numérico
                    try:
                        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                        df = df.dropna(subset=[y_col])
                    except Exception as e:
                        self.logger.warning(f"Não foi possível converter {y_col} para numérico: {e}")
                        # Se não puder converter, usar contagem
                        df = df.groupby(x_col).size().reset_index(name='count')
                        y_col = 'count'

            if df.empty or df[y_col].sum() == 0:
                raise ValueError("Nenhum dado numérico válido para gráfico de pizza")

            # Filtrar valores negativos para pizza
            df = df[df[y_col] > 0]

            # Matplotlib
            wedges, texts, autotexts = ax.pie(
                df[y_col],
                labels=df[x_col].astype(str),
                autopct='%1.1f%%',
                colors=sns.color_palette("husl", len(df))
            )
            ax.axis('equal')

            # Plotly
            fig_plotly = px.pie(
                df, values=y_col, names=x_col,
                title=f"Distribuição de {y_col.replace('_', ' ').title()}"
            )
            fig_plotly.update_traces(textposition='inside', textinfo='percent+label')

            return plt.gcf(), fig_plotly

        except Exception as e:
            self.logger.error(f"Erro na criação de gráfico de pizza: {e}")
            raise

    def _create_line_charts(self, df: pd.DataFrame, x_col: str,
                            y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de linha matplotlib e plotly."""
        try:
            # Garantir que y é numérico
            if df[y_col].dtype not in [np.number]:
                try:
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                    df = df.dropna(subset=[y_col])
                except Exception as e:
                    self.logger.warning(f"Não foi possível converter {y_col} para numérico: {e}")
                    # Se não puder converter, usar contagem
                    df = df.groupby(x_col).size().reset_index(name='count')
                    y_col = 'count'

            if df.empty:
                raise ValueError("Nenhum dado numérico válido para gráfico de linha")

            # Se x for categórico, usar índices numéricos
            if df[x_col].dtype == 'object':
                x_values = range(len(df))
                ax.plot(x_values, df[y_col], marker='o', linewidth=2, markersize=6)
                ax.set_xticks(x_values)
                ax.set_xticklabels(df[x_col].astype(str), rotation=45, ha='right')
            else:
                ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6)

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
            self.logger.error(f"Erro na criação de gráfico de linha: {e}")
            raise

    def _create_scatter_charts(self, df: pd.DataFrame, x_col: str,
                               y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de dispersão matplotlib e plotly."""
        try:
            # Garantir que ambas as colunas são numéricas
            for col in [x_col, y_col]:
                if df[col].dtype not in [np.number]:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception as e:
                        self.logger.warning(f"Não foi possível converter {col} para numérico: {e}")
                        # Se não puder converter, usar fallback
                        return self._create_fallback_chart(df)

            df = df.dropna(subset=[x_col, y_col])

            if df.empty:
                raise ValueError(
                    "Nenhum dado numérico válido para gráfico de dispersão")

            # Matplotlib
            ax.scatter(df[x_col], df[y_col], alpha=0.6, s=100)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            ax.grid(True, alpha=0.3)

            # Plotly
            fig_plotly = px.scatter(
                df, x=x_col, y=y_col, title=f"{
                    y_col.replace(
                        '_', ' ').title()} vs {
                    x_col.replace(
                        '_', ' ').title()}")

            return plt.gcf(), fig_plotly

        except Exception as e:
            self.logger.error(f"Erro na criação de gráfico de dispersão: {e}")
            raise

    def generate_summary(self, df: pd.DataFrame, interpretation: Dict[str, Any]) -> str:
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

            if tipo_analise == "ranking":
                summary_parts.extend(self._analyze_ranking(df, numeric_cols))
            elif tipo_analise == "distribuicao":
                summary_parts.extend(self._analyze_distribution(df, numeric_cols))
            elif tipo_analise == "tendencia":
                summary_parts.extend(self._analyze_trend(df, numeric_cols))
            elif tipo_analise == "comparacao":
                summary_parts.extend(self._analyze_comparison(df, numeric_cols))
            else:
                summary_parts.extend(self._analyze_general_kpis(df, numeric_cols))

            # Insights adicionais
            if len(numeric_cols) > 0:
                summary_parts.extend(self._generate_insights(df, numeric_cols))

            return "\n\n".join(summary_parts)

        except Exception as e:
            self.logger.error(f"Erro na geração do resumo: {e}")
            return f"⚠️ **Dados obtidos**: {
                len(df)} registros. Resumo detalhado indisponível."

    def _analyze_ranking(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[str]:
        """Análise específica para rankings."""
        insights = []

        if len(numeric_cols) > 0:
            valor_col = numeric_cols[0]
            categoria_col = df.columns[0]

            # Top performers
            top_1 = df.iloc[0]
            insights.append(
                f"🥇 **Líder**: {top_1[categoria_col]} com {top_1[valor_col]:,.2f}")

            if len(df) > 1:
                diferenca = top_1[valor_col] - df.iloc[1][valor_col]
                if df.iloc[1][valor_col] != 0:  # Evitar divisão por zero
                    percentual = (diferenca / df.iloc[1][valor_col]) * 100
                    insights.append(
                        f"📊 **Vantagem do líder**: {diferenca:,.2f} ({percentual:.1f}% superior)")

            # Estatísticas
            total = df[valor_col].sum()
            media = df[valor_col].mean()
            insights.append(f"💰 **Total geral**: {total:,.2f}")
            insights.append(f"📊 **Média**: {media:,.2f}")

        return insights

    def _analyze_distribution(
            self,
            df: pd.DataFrame,
            numeric_cols: List[str]) -> List[str]:
        """Análise específica para distribuições."""
        insights = []

        if len(numeric_cols) > 0:
            valor_col = numeric_cols[0]
            total = df[valor_col].sum()

            if total > 0:  # Evitar divisão por zero
                # Concentração
                top_3_percent = (df.head(3)[valor_col].sum() / total) * 100
                insights.append(
                    f"🎯 **Concentração**: Top 3 representam {top_3_percent:.1f}% do total")

                # Distribuição
                if len(df) > 4:
                    categoria_col = df.columns[0]
                    menor = df.iloc[-1]
                    insights.append(
                        f"📉 **Menor participação**: {menor[categoria_col]} ({menor[valor_col]:,.2f})")

        return insights

    def _analyze_trend(self, df: pd.DataFrame, numeric_cols: List[str]) -> List[str]:
        """Análise específica para tendências."""
        insights = []

        if len(numeric_cols) > 0 and len(df) > 1:
            valor_col = numeric_cols[0]

            # Crescimento
            primeiro = df.iloc[0][valor_col]
            ultimo = df.iloc[-1][valor_col]

            if primeiro != 0:  # Evitar divisão por zero
                crescimento = ((ultimo - primeiro) / primeiro) * 100

                if crescimento > 0:
                    insights.append(
                        f"📈 **Tendência**: Crescimento de {crescimento:.1f}%")
                else:
                    insights.append(
                        f"📉 **Tendência**: Queda de {abs(crescimento):.1f}%")

            # Volatilidade
            if df[valor_col].mean() != 0:  # Evitar divisão por zero
                volatilidade = df[valor_col].std()
                media = df[valor_col].mean()
                cv = (volatilidade / media) * 100
                insights.append(
                    f"📊 **Volatilidade**: {cv:.1f}% (coeficiente de variação)")

        return insights

    def _analyze_comparison(
            self,
            df: pd.DataFrame,
            numeric_cols: List[str]) -> List[str]:
        """Análise específica para comparações."""
        insights = []

        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            try:
                correlacao = df[col1].corr(df[col2])

                if not pd.isna(correlacao) and abs(correlacao) > 0.7:
                    tipo = "forte" if abs(correlacao) > 0.8 else "moderada"
                    direcao = "positiva" if correlacao > 0 else "negativa"
                    insights.append(
                        f"🔗 **Correlação {tipo} {direcao}**: {correlacao:.2f}")
            except BaseException:
                pass  # Ignorar erros de correlação

        return insights

    def _analyze_general_kpis(
            self,
            df: pd.DataFrame,
            numeric_cols: List[str]) -> List[str]:
        """Análise geral de KPIs."""
        insights = []

        for col in numeric_cols[:2]:  # Máximo 2 colunas numéricas
            try:
                total = df[col].sum()
                media = df[col].mean()
                insights.append(
                    f"📊 **{col.replace('_', ' ').title()}**: Total {total:,.2f} | Média {media:,.2f}")
            except BaseException:
                continue

        return insights

    def _generate_insights(
            self,
            df: pd.DataFrame,
            numeric_cols: List[str]) -> List[str]:
        """Gera insights adicionais baseados nos dados."""
        insights = []

        try:
            # Outliers
            for col in numeric_cols[:1]:  # Apenas primeira coluna numérica
                try:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = df[(df[col] < Q1 - 1.5 * IQR)
                                  | (df[col] > Q3 + 1.5 * IQR)]

                    if len(outliers) > 0:
                        insights.append(
                            f"⚠️ **Outliers detectados**: {len(outliers)} valores atípicos")
                except BaseException:
                    continue

            # Padrões
            if len(df) >= 5:
                categoria_col = df.columns[0]
                if df[categoria_col].dtype == 'object':
                    categorias_distintas = df[categoria_col].nunique()
                    insights.append(
                        f"📋 **Diversidade**: {categorias_distintas} categorias distintas")

        except Exception:
            pass  # Insights opcionais, não quebrar se falhar

        return insights

    def format_complete_response(self, df: pd.DataFrame, interpretation: Dict[str, Any],
                                 user_input: str) -> Dict[str, Any]:
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
            mpl_fig, plotly_fig = self.create_visualizations(df, interpretation)
            response["matplotlib_fig"] = mpl_fig
            response["plotly_fig"] = plotly_fig

            self.logger.info(f"Resposta completa gerada com {len(df)} registros")

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
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}")

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