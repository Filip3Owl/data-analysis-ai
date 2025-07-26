import sqlite3
from sqlite3 import Error
import pandas as pd
from typing import Optional, List, Union, Tuple, Dict
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador de banco de dados SQLite.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Validar se o arquivo existe
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Arquivo do banco de dados não encontrado: {db_path}")
        
        # Validar se o arquivo não está vazio
        if Path(db_path).stat().st_size == 0:
            raise ValueError(f"Arquivo do banco de dados está vazio: {db_path}")
    
    def connect(self) -> bool:
        """Estabelece conexão com o banco de dados SQLite."""
        try:
            # Usar timeout para evitar travamentos
            self.conn = sqlite3.connect(
                self.db_path, 
                timeout=30.0,
                check_same_thread=False  # Para uso com Streamlit
            )
            
            # Configurações recomendadas para performance e integridade
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = 10000")
            self.conn.execute("PRAGMA temp_store = MEMORY")
            
            # Testar a conexão com uma query simples
            self.conn.execute("SELECT 1").fetchone()
            
            self.logger.info("Conexão com banco de dados estabelecida com sucesso")
            return True
            
        except Error as e:
            error_msg = f"Erro ao conectar ao banco de dados: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return False
        except Exception as e:
            error_msg = f"Erro inesperado na conexão: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, List]:
        """
        Obtém informações completas de uma tabela.
        
        Returns:
            Dict com 'columns', 'types', 'primary_keys'
        """
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
            
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(?)", (table_name,))
            info = cursor.fetchall()
            
            if not info:
                return {"columns": [], "types": [], "primary_keys": []}
            
            columns = [col[1] for col in info]  # Nome da coluna
            types = [col[2] for col in info]    # Tipo da coluna
            primary_keys = [col[1] for col in info if col[5]]  # Chaves primárias
            
            return {
                "columns": columns,
                "types": types, 
                "primary_keys": primary_keys
            }
            
        except Error as e:
            error_msg = f"Erro ao obter informações da tabela {table_name}: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return {"columns": [], "types": [], "primary_keys": []}
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Obtém lista de colunas de uma tabela (mantido para compatibilidade)."""
        return self.get_table_info(table_name)["columns"]
    
    def get_all_tables(self) -> List[str]:
        """Obtém lista de todas as tabelas no banco."""
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
                
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            return [table[0] for table in cursor.fetchall()]
            
        except Error as e:
            error_msg = f"Erro ao obter lista de tabelas: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return []
    
    def get_table_count(self, table_name: str) -> int:
        """Obtém o número de registros em uma tabela."""
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
                
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
            
        except Error as e:
            error_msg = f"Erro ao contar registros da tabela {table_name}: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return 0
    
    def execute_query(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> pd.DataFrame:
        """
        Executa query e retorna DataFrame.
        
        Args:
            query: String SQL
            params: Parâmetros (tupla ou dicionário)
        """
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
            
            # Log da query para debug (sem parâmetros sensíveis)
            self.logger.debug(f"Executando query: {query[:100]}...")
            
            # Executar query com timeout implícito
            result = pd.read_sql_query(query, self.conn, params=params)
            
            self.logger.info(f"Query executada com sucesso. Retornadas {len(result)} linhas")
            return result
            
        except pd.io.sql.DatabaseError as e:
            error_msg = f"Erro de banco na query: {e}\nQuery: {query}"
            self.logger.error(error_msg)
            print(error_msg)
            return pd.DataFrame()
        except Error as e:
            error_msg = f"Erro SQLite na query: {e}\nQuery: {query}"
            self.logger.error(error_msg)
            print(error_msg)
            return pd.DataFrame()
        except Exception as e:
            error_msg = f"Erro inesperado na query: {e}\nQuery: {query}"
            self.logger.error(error_msg)
            print(error_msg)
            return pd.DataFrame()
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Valida uma query SQL sem executá-la.
        
        Returns:
            Tuple[bool, str]: (é_válida, mensagem_erro)
        """
        try:
            if not self.conn:
                return False, "Conexão não estabelecida"
            
            # Usar EXPLAIN para validar a query sem executar
            cursor = self.conn.cursor()
            cursor.execute(f"EXPLAIN {query}")
            return True, "Query válida"
            
        except Error as e:
            return False, f"Query inválida: {e}"
        except Exception as e:
            return False, f"Erro na validação: {e}"
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica se uma tabela existe no banco."""
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
                
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            exists = cursor.fetchone() is not None
            
            self.logger.debug(f"Tabela {table_name} {'existe' if exists else 'não existe'}")
            return exists
            
        except Error as e:
            error_msg = f"Erro ao verificar tabela {table_name}: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return False
    
    def get_database_schema(self) -> Dict[str, Dict]:
        """
        Retorna o schema completo do banco de dados.
        
        Returns:
            Dict com informações de todas as tabelas
        """
        schema = {}
        tables = self.get_all_tables()
        
        for table in tables:
            schema[table] = {
                **self.get_table_info(table),
                "count": self.get_table_count(table)
            }
        
        return schema
    
    def health_check(self) -> Dict[str, Union[bool, int, str]]:
        """
        Verifica a saúde do banco de dados.
        
        Returns:
            Dict com status do banco
        """
        health = {
            "connected": False,
            "tables_count": 0,
            "total_records": 0,
            "errors": []
        }
        
        try:
            if not self.conn:
                health["errors"].append("Conexão não estabelecida")
                return health
            
            health["connected"] = True
            
            # Contar tabelas
            tables = self.get_all_tables()
            health["tables_count"] = len(tables)
            
            # Contar registros totais
            total_records = 0
            for table in tables:
                count = self.get_table_count(table)
                total_records += count
                
                if count == 0:
                    health["errors"].append(f"Tabela {table} está vazia")
            
            health["total_records"] = total_records
            
            if total_records == 0:
                health["errors"].append("Nenhum registro encontrado no banco")
            
        except Exception as e:
            health["errors"].append(f"Erro no health check: {e}")
        
        return health
    
    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            try:
                self.conn.close()
                self.logger.info("Conexão com banco de dados fechada")
            except Error as e:
                error_msg = f"Erro ao fechar conexão: {e}"
                self.logger.error(error_msg)
                print(error_msg)
            finally:
                self.conn = None
    
    def __enter__(self):
        """Suporte para uso com 'with' statement."""
        if not self.connect():
            raise ConnectionError("Falha ao estabelecer conexão com o banco")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garante que a conexão será fechada."""
        self.close()
    
    def __del__(self):
        """Destructor para garantir fechamento da conexão."""
        self.close()

# Exemplo de uso com diagnóstico
def test_database_manager(db_path: str):
    """Função de teste para o DatabaseManager."""
    try:
        with DatabaseManager(db_path) as db:
            # Health check
            health = db.health_check()
            print("=== HEALTH CHECK ===")
            for key, value in health.items():
                print(f"{key}: {value}")
            
            # Schema
            schema = db.get_database_schema()
            print("\n=== SCHEMA ===")
            for table, info in schema.items():
                print(f"\n{table}:")
                print(f"  Colunas: {info['columns']}")
                print(f"  Registros: {info['count']}")
            
            return True
            
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False