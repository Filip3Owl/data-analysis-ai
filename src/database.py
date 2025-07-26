import sqlite3
from sqlite3 import Error
import pandas as pd
from typing import Optional, List, Union, Tuple, Dict  # Adicionando Dict aqui

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador de banco de dados SQLite.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> bool:
        """Estabelece conexão com o banco de dados SQLite."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Configurações recomendadas
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            return True
        except Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Obtém lista de colunas de uma tabela."""
        try:
            if not self.conn:
                raise Error("Conexão não estabelecida")
                
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(?)", (table_name,))
            return [column[1] for column in cursor.fetchall()]
        except Error as e:
            print(f"Erro ao obter colunas: {e}")
            return []
    
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
                
            return pd.read_sql_query(query, self.conn, params=params)
        except Error as e:
            print(f"Erro na query: {e}\nQuery: {query}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return pd.DataFrame()
    
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
            return cursor.fetchone() is not None
        except Error as e:
            print(f"Erro ao verificar tabela: {e}")
            return False
    
    def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            try:
                self.conn.close()
            except Error as e:
                print(f"Erro ao fechar conexão: {e}")
            finally:
                self.conn = None
    
    def __enter__(self):
        """Suporte para uso com 'with' statement."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garante que a conexão será fechada."""
        self.close()