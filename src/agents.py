from langchain.llms import OpenAI
from src.prompts import INTERPRETATION_PROMPT, SQL_PROMPT, FORMATTING_PROMPT
import json
from typing import Dict, Any, Optional

class AgentsManager:
    def __init__(self, llm: OpenAI, db_manager=None):
        """
        Inicializa o gerenciador de agentes com LLM e gerenciador de banco de dados.
        
        Args:
            llm: Instância do modelo de linguagem
            db_manager: Gerenciador de banco de dados (opcional)
        """
        self.llm = llm
        self.db_manager = db_manager
    
    def interpret_request(self, user_input: str) -> Dict[str, Any]:
        """
        Interpreta a solicitação do usuário e retorna uma estrutura JSON.
        
        Args:
            user_input: Entrada do usuário em linguagem natural
            
        Returns:
            Dicionário com a interpretação estruturada ou mensagem de erro
        """
        try:
            prompt = INTERPRETATION_PROMPT.format(user_input=user_input)
            response = self.llm(prompt)
            
            # Verificação básica da resposta antes do parse
            if not response.strip().startswith('{') or not response.strip().endswith('}'):
                raise json.JSONDecodeError("Resposta não está no formato JSON", response, 0)
                
            parsed = json.loads(response)
            
            # Validação mínima da estrutura
            required_keys = ["tabelas", "filtros", "agregacoes"]
            if not all(key in parsed for key in required_keys):
                raise ValueError("Estrutura de interpretação incompleta")
                
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {str(e)}")
            return {"error": "Falha na interpretação - formato inválido"}
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")
            return {"error": f"Erro na interpretação: {str(e)}"}
    
    def generate_sql(self, interpretation: Dict[str, Any]) -> str:
        """
        Gera uma query SQL válida baseada na interpretação.
        
        Args:
            interpretation: Dicionário com a interpretação estruturada
            
        Returns:
            Query SQL ou mensagem de erro
        """
        try:
            if not isinstance(interpretation, dict):
                raise ValueError("Interpretação deve ser um dicionário")
            
            if "error" in interpretation:
                return f"SELECT '{interpretation['error']}' AS erro"
            
            # Verificação de tabelas necessárias
            required_tables = interpretation.get("tabelas", [])
            if not required_tables:
                return "SELECT 'Nenhuma tabela especificada' AS erro"
            
            # Verificação especial para campanhas
            if "campanhas" in required_tables:
                if not self.db_manager:
                    return "SELECT 'Gerenciador de banco não disponível' AS erro"
                    
                if not self.db_manager.table_exists("campanhas_marketing"):
                    return "SELECT 'Tabela de campanhas não encontrada' AS erro"
                    
                columns = self.db_manager.get_table_columns("campanhas_marketing")
                if not all(col in columns for col in ["canal", "interagiu"]):
                    return "SELECT 'Tabela campanhas_marketing está incompleta' AS erro"
            
            # Obter schema apenas para tabelas existentes
            schema_info = {
                table: self._get_table_schema(table)
                for table in required_tables
                if self._table_exists(table)
            }
            
            prompt = SQL_PROMPT.format(
                interpretation=json.dumps(interpretation, indent=2),
                schema_info=json.dumps(schema_info, indent=2)
            )
            
            generated_sql = self.llm(prompt).strip()
            
            # Validação básica da SQL gerada
            if not generated_sql.lower().startswith(('select', 'with', 'insert', 'update', 'delete')):
                raise ValueError(f"SQL inválida gerada: {generated_sql}")
                
            return generated_sql
            
        except Exception as e:
            print(f"Erro ao gerar SQL: {str(e)}")
            return f"SELECT 'Erro ao gerar query: {str(e)}' AS erro"
    
    def _table_exists(self, table_name: str) -> bool:
        """Verifica se uma tabela existe no banco de dados."""
        if not self.db_manager:
            return False
        return self.db_manager.table_exists(table_name)
    
    def _get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Obtém o schema de uma tabela específica.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com {nome_coluna: tipo}
        """
        # Schema básico para tabelas conhecidas
        predefined_schemas = {
            "clientes": {
                "id": "INTEGER", "nome": "TEXT", "email": "TEXT", 
                "idade": "INTEGER", "cidade": "TEXT", "estado": "TEXT",
                "profissao": "TEXT", "genero": "TEXT"
            },
            "compras": {
                "id": "INTEGER", "cliente_id": "INTEGER", "data_compra": "TEXT",
                "valor": "REAL", "categoria": "TEXT", "canal": "TEXT"
            },
            "campanhas_marketing": {
                "id": "INTEGER", "cliente_id": "INTEGER", "nome_campanha": "TEXT",
                "data_envio": "TEXT", "interagiu": "BOOLEAN", "canal": "TEXT"
            },
            "suporte": {
                "id": "INTEGER", "cliente_id": "INTEGER", "data_contato": "TEXT",
                "tipo_contato": "TEXT", "resolvido": "BOOLEAN", "canal": "TEXT"
            }
        }
        
        # Tenta obter do banco se existir, senão usa o pré-definido
        if self.db_manager and self.db_manager.table_exists(table_name):
            columns = self.db_manager.get_table_columns(table_name)
            return {col: "TEXT" for col in columns}  # Tipo genérico se não soubermos
        return predefined_schemas.get(table_name, {})
    
    def format_response(self, results_json: str, original_question: str) -> str:
        """
        Formata os resultados em uma resposta amigável.
        
        Args:
            results_json: Resultados em formato JSON
            original_question: Pergunta original do usuário
            
        Returns:
            Resposta formatada ou mensagem de erro
        """
        try:
            # Verificação básica do JSON
            if not results_json.strip():
                raise ValueError("Resultados vazios")
                
            prompt = FORMATTING_PROMPT.format(
                original_question=original_question,
                query_results=results_json
            )
            
            response = self.llm(prompt)
            
            # Limpeza básica da resposta
            response = response.strip()
            if response.startswith(('"', "'")) and response.endswith(('"', "'")):
                response = response[1:-1]
                
            return response
            
        except json.JSONDecodeError:
            return "Erro: Não foi possível formatar os resultados (JSON inválido)"
        except Exception as e:
            return f"Erro ao formatar resposta: {str(e)}"