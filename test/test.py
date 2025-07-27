import sqlite3

# Caminho do banco de dados
caminho_banco = r'data\clientes_completo.db'  # Substitua pelo caminho correto
conexao = sqlite3.connect(caminho_banco)
cursor = conexao.cursor()

def listar_tabelas():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [linha[0] for linha in cursor.fetchall()]

def verificar_chaves_estrangeiras():
    tabelas = listar_tabelas()
    relacionamentos = []

    for tabela in tabelas:
        cursor.execute(f"PRAGMA foreign_key_list({tabela})")
        fks = cursor.fetchall()
        if fks:
            print(f"\n🔗 Tabela: {tabela} possui chaves estrangeiras:")
            for fk in fks:
                id_, seq, tabela_referenciada, coluna_origem, coluna_referenciada, on_update, on_delete, match = fk
                print(f"  - {coluna_origem} → {tabela_referenciada}.{coluna_referenciada}")
                relacionamentos.append((tabela, coluna_origem, tabela_referenciada, coluna_referenciada))
        else:
            print(f"\nℹ️ Tabela: {tabela} não possui chaves estrangeiras declaradas.")
    
    return relacionamentos

verificar_chaves_estrangeiras()
conexao.close()
