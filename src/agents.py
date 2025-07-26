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

try:
    from .prompts import INTERPRETATION_PROMPT, SQL_PROMPT, FORMATTING_PROMPT, ERROR_PROMPT
except ImportError:
    # Fallback se não conseguir importar
    from langchain.prompts import PromptTemplate
    
    INTERPRETATION_PROMPT = PromptTemplate(
        input_variables=["user_input"],
        template="""
        Analise a solicitação e retorne um JSON estruturado:
        Solicitação: "{user_input}"
        
        Retorne apenas:
        {{
            "intencao": "descrição",
            "tipo_analise": "ranking|distribuicao|tendencia|kpi",
            "tabelas": ["tabelas necessárias"],
            "metricas": ["métricas"],
            "dimensoes": ["agrupamentos"],
            "filtros": ["condições"],
            "limite": 10,
            "tipo_grafico": "barras|pizza|linha|tabela",
            "formato_saida": "completo"
        }}
        """
    )
    
    SQL_PROMPT = PromptTemplate(
        input_variables=["interpretation"],
        template="""
        Gere uma query SQL válida para SQLite baseada em: {interpretation}
        
        Tabelas disponíveis:
        - clientes(id, nome, email, idade, cidade, estado, profissao, genero)
        - compras(id, cliente_id, data_compra, valor, categoria, canal)
        - suporte(id, cliente_id, data_contato, tipo_contato, resolvido, canal)
        - campanhas_marketing(id, cliente_id, nome_campanha, data_envio, interagiu, canal)
        
        Retorne APENAS a query SQL.
        """
    )

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
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')
        
        try:
            sns.set_palette("husl")
        except:
            pass
        
        # Schema do banco para referência
        self.schema = {
            "clientes": ["id", "nome", "email", "idade", "cidade", "estado", "profissao", "genero"],
            "compras": ["id", "cliente_id", "data_compra", "valor", "categoria", "canal"],
            "suporte": ["id", "cliente_id", "data_contato", "tipo_contato", "resolvido", "canal"],
            "campanhas_marketing": ["id", "cliente_id", "nome_campanha", "data_envio", "interagiu", "canal"]
        }
    
    def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """
        Interpreta a solicitação do usuário e determina o tipo de análise.
        
        Args:
            user_input: Pergunta do usuário
            
        Returns:
            Dict com interpretação estruturada
        """
        try:
            # Usar o prompt template
            prompt = INTERPRETATION_PROMPT.format(user_input=user_input)
            response = self.llm(prompt)
            
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
            # Usar o prompt template
            prompt = SQL_PROMPT.format(interpretation=json.dumps(interpretation, indent=2))
            response = self.llm(prompt)
            
            # Limpar resposta
            sql_query = re.sub(r'^```sql\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
            sql_query = sql_query.strip()
            
            # Validar query se possível
            try:
                is_valid, error_msg = self.db.validate_query(sql_query)
                if not is_valid:
                    self.logger.error(f"Query inválida: {error_msg}")
                    # Tentar uma query básica como fallback
                    sql_query = "SELECT * FROM clientes LIMIT 10"
            except:
                pass  # Se não conseguir validar, continua com a query
            
            self.logger.info(f"Query SQL gerada: {sql_query}")
            return sql_query
            
        except Exception as e:
            self.logger.error(f"Erro na geração SQL: {e}")
            # Fallback para query básica
            return "SELECT * FROM clientes LIMIT 10"
    
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
                    summary += f"**{col.replace('_', ' ').title()}**: Total {total:,.2f} | Média {media:,.2f}\n"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro na formatação: {e}")
            return "⚠️ **Dados processados com sucesso**, mas houve erro na formatação."
    
    def create_visualizations(self, df: pd.DataFrame, interpretation: Dict[str, Any]) -> Tuple[Optional[Any], Optional[Any]]:
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
                fig_mpl, fig_plotly = self._create_bar_charts(df, x_col, y_col, ax)
            elif tipo_grafico == "pizza":
                fig_mpl, fig_plotly = self._create_pie_charts(df, x_col, y_col, ax)
            elif tipo_grafico == "linha":
                fig_mpl, fig_plotly = self._create_line_charts(df, x_col, y_col, ax)
            else:
                # Default para barras
                fig_mpl, fig_plotly = self._create_bar_charts(df, x_col, y_col, ax)
            
            # Configurações gerais matplotlib
            plt.title(interpretation.get("intencao", "Análise de Dados"), fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            return fig_mpl, fig_plotly
            
        except Exception as e:
            self.logger.error(f"Erro na criação de visualizações: {e}")
            return None, None
    
    def _create_bar_charts(self, df: pd.DataFrame, x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
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
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:,.0f}', ha='center', va='bottom')
            
            # Rotacionar labels se necessário
            if len(df) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Plotly
            fig_plotly = px.bar(
                df, x=x_col, y=y_col,
                title=f"{y_col.replace('_', ' ').title()} por {x_col.replace('_', ' ').title()}"
            )
            fig_plotly.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
            
            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de barras: {e}")
            return plt.gcf(), None
    
    def _create_pie_charts(self, df: pd.DataFrame, x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
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
            fig_plotly.update_traces(textposition='inside', textinfo='percent+label')
            
            return plt.gcf(), fig_plotly
        except Exception as e:
            self.logger.error(f"Erro nos gráficos de pizza: {e}")
            return plt.gcf(), None
    
    def _create_line_charts(self, df: pd.DataFrame, x_col: str, y_col: str, ax) -> Tuple[Any, Any]:
        """Cria gráficos de linha matplotlib e plotly."""
        try:
            # Matplotlib
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
            self.logger.error(f"Erro nos gráficos de linha: {e}")
            return plt.gcf(), None
    
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
            summary_parts.append(f"📊 **Resumo da Análise**: {interpretation.get('intencao', 'Análise de dados')}")
            summary_parts.append(f"📈 **Total de registros**: {total_rows:,}")
            
            # Análise por tipo
            tipo_analise = interpretation.get("tipo_analise", "kpi")
            
            if tipo_analise == "ranking" and len(numeric_cols) > 0:
                valor_col = numeric_cols[0]
                categoria_col = df.columns[0]
                
                # Top performer
                top_1 = df.iloc[0]
                summary_parts.append(f"🥇 **Líder**: {top_1[categoria_col]} com {top_1[valor_col]:,.2f}")
                
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
                    summary_parts.append(f"📊 **{col.replace('_', ' ').title()}**: Total {total:,.2f} | Média {media:,.2f}")
            
            return "\n\n".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Erro na geração do resumo: {e}")
            return f"⚠️ **Dados obtidos**: {len(df)} registros. Resumo detalhado indisponível."
    
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
            response["summary"] = f"⚠️ **Dados obtidos**: {len(df)} registros. Erro na formatação: {str(e)}"
        
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
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"R$ {x:,.2f}")
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
                html += f"<p><small><i>Mostrando 20 de {len(df)} registros totais</i></small></p>"
            
            return html
            
        except Exception as e:
            self.logger.error(f"Erro na formatação da tabela: {e}")
            return df.head(10).to_html(index=False)