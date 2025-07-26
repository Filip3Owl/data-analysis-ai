from langchain.llms import OpenAI
from src.prompts import INTERPRETATION_PROMPT, SQL_PROMPT, FORMATTING_PROMPT
import json

class AgentsManager:
    def __init__(self, llm, db_manager=None):
        self.llm = llm
        self.db_manager = db_manager
    
    def interpret_request(self, user_input):
        """Interpreta a solicitação do usuário"""
        prompt = INTERPRETATION_PROMPT.format(user_input=user_input)
        response = self.llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Falha na interpretação"}
    
    def generate_sql(self, interpretation):
        """Gera query SQL baseada na interpretação"""
        if not isinstance(interpretation, dict):
            interpretation = {"error": "Interpretação inválida"}
        
        # Verificação para tabela de campanhas
        if "campanhas" in interpretation.get("tabelas", []):
            if not self.db_manager or not self.db_manager.table_exists("campanhas_marketing"):
                return "SELECT 'Tabela de campanhas não disponível' AS erro"
            
            columns = self.db_manager.get_table_columns("campanhas_marketing")
            if "canal" not in columns or "interagiu" not in columns:
                return "SELECT 'Estrutura de campanhas incompleta' AS erro"
        
        # Geração da query SQL
        schema_info = self._get_schema_info(interpretation.get("tabelas", []))
        prompt = SQL_PROMPT.format(
            interpretation=json.dumps(interpretation, indent=2),
            schema_info=json.dumps(schema_info, indent=2)
        )
        return self.llm(prompt)
    
    def _get_schema_info(self, tables):
        """Obtém informações de schema para as tabelas"""
        schemas = {
            "clientes": {"id": "INTEGER", "nome": "TEXT", "estado": "TEXT"},
            "compras": {"id": "INTEGER", "cliente_id": "INTEGER", "valor": "REAL"},
            "campanhas_marketing": {"id": "INTEGER", "cliente_id": "INTEGER", "canal": "TEXT"}
        }
        return {table: schemas.get(table, {}) for table in tables}
    
    def format_response(self, results_json, original_question):
        """Formata a resposta final"""
        prompt = FORMATTING_PROMPT.format(
            original_question=original_question,
            query_results=results_json
        )
        return self.llm(prompt)