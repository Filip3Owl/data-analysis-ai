import sqlite3
from sqlite3 import Error
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Estabelece conexão com o banco de dados SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Ativa verificação de chaves estrangeiras
            self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return False
    
    def get_table_columns(self, table_name):
        """Obtém lista de colunas de uma tabela"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in cursor.fetchall()]
        except Error as e:
            print(f"Erro ao obter colunas da tabela {table_name}: {e}")
            return []
    
    def execute_query(self, query, params=None):
        """
        Executa query e retorna DataFrame
        Args:
            query: string SQL
            params: tupla de parâmetros (opcional)
        """
        try:
            return pd.read_sql_query(query, self.conn, params=params)
        except Error as e:
            print(f"Erro na execução da query:\nQuery: {query}\nErro: {e}")
            return pd.DataFrame()
        except pd.errors.DatabaseError as e:
            print(f"Erro no pandas ao executar query:\n{e}")
            return pd.DataFrame()
    
    def table_exists(self, table_name):
        """Verifica se uma tabela existe no banco"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            return cursor.fetchone() is not None
        except Error as e:
            print(f"Erro ao verificar tabela {table_name}: {e}")
            return False
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            try:
                self.conn.close()
            except Error as e:
                print(f"Erro ao fechar conexão: {e}")
            finally:
                self.conn = None