from langchain.prompts import PromptTemplate

# Prompt para interpretação das perguntas
INTERPRETATION_PROMPT = PromptTemplate(
    input_variables=["user_input"],
    template="""
    Você é um especialista em SQL e análise de dados. Converta a solicitação do usuário em uma estrutura JSON usando APENAS estas tabelas:
    
    ### Estrutura do Banco de Dados:
    - clientes(id, nome, email, idade, cidade, estado, profissao, genero)
    - compras(id, cliente_id, data_compra, valor, categoria, canal)
    - suporte(id, cliente_id, data_contato, tipo_contato, resolvido, canal)
    - campanhas_marketing(id, cliente_id, nome_campanha, data_envio, interagiu, canal)

    ### Solicitação do Usuário:
    "{user_input}"

    ### Instruções:
    1. Analise a pergunta e identifique quais tabelas são necessárias
    2. Determine os filtros relevantes (WHERE)
    3. Identifique as métricas a calcular (COUNT, SUM, AVG)
    4. Especifique os campos para agrupamento (GROUP BY)
    5. Defina o formato de saída desejado (tabela/gráfico/texto)

    Retorne APENAS um JSON com esta estrutura:
    {{
        "intenção": "Descrição clara do objetivo",
        "tabelas": ["lista", "de", "tabelas"],
        "filtros": ["condicao1", "condicao2"],
        "agregacoes": ["funcao(coluna) AS alias"],
        "grupo_por": ["coluna1", "coluna2"],
        "formato_saida": "tabela/gráfico/texto"
    }}

    Exemplo para "Vendas por estado em 2023":
    {{
        "intenção": "Total de vendas agrupadas por estado em 2023",
        "tabelas": ["compras", "clientes"],
        "filtros": ["strftime('%Y', data_compra) = '2023'"],
        "agregacoes": ["SUM(valor) AS total_vendas"],
        "grupo_por": ["clientes.estado"],
        "formato_saida": "gráfico"
    }}
    """
)

# Prompt para geração de SQL
SQL_PROMPT = PromptTemplate(
    input_variables=["interpretation"],
    template="""
    Você é um especialista em SQLite. Gere uma query SQL válida seguindo estas regras:

    1. Use apenas estas tabelas:
       - clientes(id,nome,email,idade,cidade,estado,profissao,genero)
       - compras(id,cliente_id,data_compra,valor,categoria,canal)
       - suporte(id,cliente_id,data_contato,tipo_contato,resolvido,canal)
       - campanhas(id,cliente_id,nome_campanha,data_envio,interagiu,canal)

    2. Relacionamentos:
       - compras.cliente_id = clientes.id
       - suporte.cliente_id = clientes.id
       - campanhas.cliente_id = clientes.id

    3. Sempre verifique se os campos usados existem nas tabelas

    4. Para datas use: strftime('%Y', data_compra) = '2024'

    5. Se a pergunta mencionar:
       - "este ano" → strftime('%Y', data) = strftime('%Y', 'now')
       - "este mês" → strftime('%Y-%m', data) = strftime('%Y-%m', 'now')

    Solicitação: {interpretation}

    Retorne APENAS a query SQL, sem explicações.
    """
)

# Prompt para formatação de respostas
FORMATTING_PROMPT = PromptTemplate(
    input_variables=["original_question", "query_results"],
    template="""
    Você é um analista de dados. Formate os resultados para o usuário final.

    ### Pergunta Original:
    {original_question}

    ### Dados Brutos (JSON):
    {query_results}

    ### Instruções:
    1. Comece com um resumo executivo (1-2 frases)
    2. Destaque insights importantes (máximos, mínimos, tendências)
    3. Formate conforme solicitado:
       - Tabelas: use Markdown com alinhamento
       - Gráficos: sugira o tipo ideal (barras, pizza, linhas)
    4. Se relevante, mostre exemplos dos dados
    5. Seja conciso (máximo 200 palavras)

    ### Exemplo para "Vendas por categoria":
    "As vendas totais por categoria são: Eletrônicos (R$12.340,00), Roupas (R$8.570,00)... 
    A categoria mais vendida foi Eletrônicos, representando 42% do total."

    ### Formato Esperado:
    - Para tabelas: use Markdown
    - Para gráficos: descreva o gráfico ideal
    - Para textos: seja direto e informativo
    """
)

# Prompt para tratamento de erros
ERROR_PROMPT = PromptTemplate(
    input_variables=["error_message", "query"],
    template="""
    Você precisa explicar um erro de banco de dados para um usuário não técnico.

    ### Erro Ocorrido:
    {error_message}

    ### Query que Causou o Erro:
    {query}

    ### Instruções:
    1. Explique o erro em linguagem simples
    2. Sugira possíveis correções
    3. Se for erro de sintaxe, aponte o provável local
    4. Mantenha o tom profissional mas acessível
    5. Limite a 100 palavras

    Exemplo:
    "Parece que há um problema com a data informada. Verifique se o formato está correto (AAAA-MM-DD) 
    e se existem registros no período solicitado."
    """
)