from langchain.prompts import PromptTemplate

INTERPRETATION_PROMPT = PromptTemplate(
    input_variables=["user_input"],
    template="""
    Você é um especialista em análise de dados. Converta a solicitação do usuário em uma estrutura JSON.

    Solicitação: {user_input}

    Retorne um JSON com:
    - "intenção": Descrição clara do que o usuário quer
    - "tabelas": Lista de tabelas necessárias (ex: ["clientes", "compras"])
    - "filtros": Condições WHERE (ex: ["data_compra >= '2024-01-01'", "canal = 'app'"])
    - "agregacoes": Métricas a calcular (ex: ["COUNT(*)", "AVG(valor)"])
    - "grupo_por": Campos para GROUP BY (ex: ["estado", "categoria"])
    - "formato_saida": "tabela", "gráfico" ou "texto"

    Exemplo para "Top 5 estados com mais clientes em 2024":
    {{
        "intenção": "Listar os 5 estados com maior número de clientes em 2024",
        "tabelas": ["clientes"],
        "filtros": ["data_cadastro >= '2024-01-01'"],
        "agregacoes": ["COUNT(id) AS total_clientes"],
        "grupo_por": ["estado"],
        "formato_saida": "tabela"
    }}

    Retorne APENAS o JSON, sem comentários ou explicações.
    """
)

SQL_PROMPT = PromptTemplate(
    input_variables=["interpretation", "schema_info"],
    template="""
    Você é um especialista em SQL. Gere uma query baseada nestes dados:

    ### Esquema do Banco de Dados:
    {schema_info}

    ### Solicitação Interpretada:
    {interpretation}

    ### Regras Obrigatórias:
    1. Use apenas os nomes de tabelas e colunas fornecidos
    2. Para datas, use o formato 'YYYY-MM-DD'
    3. Inclua todos os filtros relevantes
    4. Use JOINs quando necessário
    5. Limite os resultados quando apropriado

    ### Exemplo para referência:
    Solicitação: "Top 5 estados com mais clientes"
    SQL: SELECT estado, COUNT(*) AS total_clientes FROM clientes GROUP BY estado ORDER BY total_clientes DESC LIMIT 5

    Gere APENAS o código SQL, sem comentários ou explicações.
    """
)

FORMATTING_PROMPT = PromptTemplate(
    input_variables=["original_question", "query_results"],
    template="""
    Você é um analista de dados. Formate os resultados para o usuário final.

    ### Pergunta Original:
    {original_question}

    ### Dados Obtidos (JSON):
    {query_results}

    ### Instruções:
    1. Comece com um resumo executivo (1-2 frases)
    2. Destaque os insights mais importantes
    3. Formate os dados conforme solicitado:
       - Para "tabela": use markdown com alinhamento correto
       - Para "gráfico": sugira o tipo ideal (barras, pizza, etc.)
    4. Se relevante, sugira análises adicionais
    5. Seja conciso (máximo 150 palavras)

    ### Exemplo:
    Pergunta: "Top 5 estados com mais clientes"
    Resposta: "Os 5 estados com maior número de clientes são: 1) São Paulo (1.240 clientes), 2) Rio de Janeiro (892)... [tabela]"

    Retorne APENAS a resposta formatada, sem metadados.
    """
)