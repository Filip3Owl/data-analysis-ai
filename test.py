import sqlite3
import os
from pathlib import Path

def testar_relacionamentos(caminho_banco):
    """
    Função para testar os relacionamentos entre tabelas no banco de dados SQLite.
    
    Args:
        caminho_banco (str): Caminho relativo ou absoluto para o arquivo do banco de dados.
    """
    try:
        # Verificar se o arquivo do banco de dados existe
        if not os.path.exists(caminho_banco):
            raise FileNotFoundError(f"Arquivo do banco de dados não encontrado: {caminho_banco}")
        
        # Conectar ao banco de dados
        conexao = sqlite3.connect(caminho_banco)
        cursor = conexao.cursor()
        
        print(f"\nConexão estabelecida com o banco de dados: {caminho_banco}\n")
        
        # Obter lista de tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = [t[0] for t in cursor.fetchall()]
        
        if not tabelas:
            print("O banco de dados não contém nenhuma tabela.")
            return
        
        # Dicionário para armazenar os relacionamentos
        relacionamentos = {}
        
        # Para cada tabela, identificar chaves estrangeiras
        for tabela in tabelas:
            cursor.execute(f"PRAGMA foreign_key_list({tabela});")
            fks = cursor.fetchall()
            
            if fks:
                relacionamentos[tabela] = []
                for fk in fks:
                    # Estrutura do resultado: (id, seq, table, from, to, on_update, on_delete, match)
                    relacionamento = {
                        'tabela_origem': tabela,
                        'coluna_origem': fk[3],
                        'tabela_destino': fk[2],
                        'coluna_destino': fk[4],
                        'on_update': fk[5],
                        'on_delete': fk[6]
                    }
                    relacionamentos[tabela].append(relacionamento)
        
        # Exibir os relacionamentos encontrados
        if not any(relacionamentos.values()):
            print("Nenhum relacionamento (chave estrangeira) encontrado no banco de dados.")
            return
        
        print("\nRELACIONAMENTOS ENCONTRADOS:")
        for tabela, rels in relacionamentos.items():
            if rels:
                print(f"\nTabela '{tabela}':")
                for rel in rels:
                    print(f"  → Coluna '{rel['coluna_origem']}' referencia:")
                    print(f"     Tabela: '{rel['tabela_destino']}'")
                    print(f"     Coluna: '{rel['coluna_destino']}'")
                    print(f"     On Update: {rel['on_update']}")
                    print(f"     On Delete: {rel['on_delete']}")
                    print("     " + "-"*40)
        
        # Verificar integridade dos relacionamentos
        print("\nTESTANDO INTEGRIDADE DOS RELACIONAMENTOS:")
        
        # Verificar se as chaves estrangeiras estão habilitadas
        cursor.execute("PRAGMA foreign_keys;")
        fk_enabled = cursor.fetchone()[0]
        print(f"Chaves estrangeiras habilitadas: {'Sim' if fk_enabled else 'Não'}")
        
        if fk_enabled:
            # Testar a integridade referencial
            try:
                cursor.execute("PRAGMA foreign_key_check;")
                problemas = cursor.fetchall()
                
                if problemas:
                    print("\nPROBLEMAS DE INTEGRIDADE ENCONTRADOS:")
                    for prob in problemas:
                        print(f"Tabela: {prob[0]}, Linha: {prob[1]}, Problema: {prob[2]}")
                else:
                    print("\nNenhum problema de integridade referencial encontrado.")
            except sqlite3.Error as e:
                print(f"Erro ao verificar integridade: {e}")
        
        # Fechar conexão
        conexao.close()
        print("\nTeste de relacionamentos concluído!")
        
    except sqlite3.Error as e:
        print(f"\nErro ao acessar o banco de dados: {e}")
    except Exception as e:
        print(f"\nErro inesperado: {e}")

if __name__ == "__main__":
    # Definir o caminho relativo para o banco de dados
    caminho_relativo = Path("data") / "clientes_completo.db"
    
    # Converter para caminho absoluto para facilitar a visualização
    caminho_absoluto = caminho_relativo.absolute()
    
    print(f"Testando os relacionamentos no banco de dados em: {caminho_absoluto}")
    testar_relacionamentos(caminho_relativo)