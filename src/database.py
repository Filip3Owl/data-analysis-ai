import sqlite3
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Optional, Union

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de conexão e operações com banco de dados SQLite."""

    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador de banco de dados.

        Args:
            db_path (str): Caminho para o arquivo do banco de dados
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Garante que o arquivo de banco existe."""
        if not self.db_path.exists():
            logger.warning(f"Banco de dados não encontrado: {self.db_path}")
            # Criar diretório se não existir
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """
        Estabelece conexão com o banco de dados.

        Returns:
            bool: True se conexão foi estabelecida com sucesso
        """
        try:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Conexão estabelecida com {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Conexão fechada")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def execute_query(self, query: str, params: tuple = None) -> Optional[pd.DataFrame]:
        """
        Executa uma query SQL e retorna o resultado como DataFrame.

        Args:
            query (str): Query SQL para executar
            params (tuple, optional): Parâmetros para a query

        Returns:
            pd.DataFrame: Resultado da query ou None se erro
        """
        if not self.connection:
            if not self.connect():
                return None

        try:
            logger.info(f"Executando query: {query[:100]}...")

            if params:
                result = pd.read_sql_query(query, self.connection, params=params)
            else:
                result = pd.read_sql_query(query, self.connection)

            logger.info(
                f"Query executada com sucesso. Resultados: {
                    len(result)} linhas")
            return result

        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.error(f"Query: {query}")
            return None

    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Obtém a lista de colunas de uma tabela específica.

        Args:
            table_name (str): Nome da tabela

        Returns:
            List[str]: Lista de nomes de colunas
        """
        if not self.connection:
            if not self.connect():
                return []

        try:
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(query)
            
            if result is not None and len(result) > 0:
                return result['name'].tolist()
            return []
            
        except Exception as e:
            logger.error(f"Erro ao obter colunas da tabela {table_name}: {e}")
            return []

    def get_database_schema(self) -> Dict:
        """
        Obtém o schema completo do banco de dados.

        Returns:
            Dict: Dicionário com informações das tabelas
        """
        if not self.connection:
            if not self.connect():
                return {}

        try:
            schema = {}

            # Obter lista de tabelas
            tables_query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            tables_df = self.execute_query(tables_query)

            if tables_df is None or len(tables_df) == 0:
                return {}

            for _, row in tables_df.iterrows():
                table_name = row['name']

                # Obter informações da tabela
                table_info_query = f"PRAGMA table_info({table_name})"
                table_info_df = self.execute_query(table_info_query)

                # Obter contagem de registros
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_df = self.execute_query(count_query)

                columns = []
                types = []

                if table_info_df is not None:
                    columns = table_info_df['name'].tolist()
                    types = table_info_df['type'].tolist()

                record_count = 0
                if count_df is not None and len(count_df) > 0:
                    record_count = count_df.iloc[0]['count']

                schema[table_name] = {
                    'columns': columns,
                    'types': types,
                    'count': record_count
                }

            return schema

        except Exception as e:
            logger.error(f"Erro ao obter schema: {e}")
            return {}

    def get_all_tables(self) -> List[str]:
        """
        Obtém lista de todas as tabelas no banco.

        Returns:
            List[str]: Lista com nomes das tabelas
        """
        try:
            query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            result = self.execute_query(query)

            if result is not None and len(result) > 0:
                return result['name'].tolist()
            else:
                return []

        except Exception as e:
            logger.error(f"Erro ao obter tabelas: {e}")
            return []

    def health_check(self) -> Dict:
        """
        Verifica a saúde do banco de dados.

        Returns:
            Dict: Status do banco de dados
        """
        health_status = {
            'connected': False,
            'tables_count': 0,
            'total_records': 0,
            'errors': []
        }

        try:
            # Verificar conexão
            if not self.connection:
                if not self.connect():
                    health_status['errors'].append("Falha na conexão")
                    return health_status

            health_status['connected'] = True

            # Obter tabelas
            tables = self.get_all_tables()
            health_status['tables_count'] = len(tables)

            # Contar registros totais
            total_records = 0
            for table in tables:
                try:
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    result = self.execute_query(count_query)
                    if result is not None and len(result) > 0:
                        total_records += result.iloc[0]['count']
                except Exception as e:
                    health_status['errors'].append(f"Erro na tabela {table}: {e}")

            health_status['total_records'] = total_records

        except Exception as e:
            health_status['errors'].append(f"Erro geral: {e}")

        return health_status

    def execute_raw_query(self, query: str,
                          params: tuple = None) -> Optional[List[Dict]]:
        """
        Executa uma query e retorna resultado como lista de dicionários.

        Args:
            query (str): Query SQL
            params (tuple, optional): Parâmetros

        Returns:
            List[Dict]: Resultado da query
        """
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Converter resultado para lista de dicionários
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))

            return result

        except Exception as e:
            logger.error(f"Erro ao executar query raw: {e}")
            return None

    def insert_data(self, table_name: str, data: Union[Dict, pd.DataFrame]) -> bool:
        """
        Insere dados em uma tabela.

        Args:
            table_name (str): Nome da tabela
            data (Dict ou DataFrame): Dados para inserir

        Returns:
            bool: True se inserção foi bem-sucedida
        """
        if not self.connection:
            if not self.connect():
                return False

        try:
            if isinstance(data, dict):
                # Inserir um registro
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

                cursor = self.connection.cursor()
                cursor.execute(query, tuple(data.values()))
                self.connection.commit()

            elif isinstance(data, pd.DataFrame):
                # Inserir DataFrame
                data.to_sql(
                    table_name,
                    self.connection,
                    if_exists='append',
                    index=False)

            logger.info(f"Dados inseridos na tabela {table_name}")
            return True

        except Exception as e:
            logger.error(f"Erro ao inserir dados: {e}")
            return False

    def create_table_from_dataframe(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Cria uma tabela baseada na estrutura de um DataFrame.

        Args:
            table_name (str): Nome da tabela
            df (pd.DataFrame): DataFrame com estrutura desejada

        Returns:
            bool: True se tabela foi criada
        """
        if not self.connection:
            if not self.connect():
                return False

        try:
            df.to_sql(table_name, self.connection, if_exists='replace', index=False)
            logger.info(f"Tabela {table_name} criada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabela: {e}")
            return False