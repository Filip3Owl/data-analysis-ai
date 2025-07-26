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
    3. Identifique as métricas a calcular (COUNT, SUM, AVG, etc.)
    4. Especifique os campos para agrupamento (GROUP BY)
    5. Defina o formato de saída desejado (tabela/gráfico/texto)
    6. Para ordenação, considere ORDER BY quando relevante

    Retorne APENAS um JSON válido com esta estrutura:
    {{
        "intencao": "Descrição clara do objetivo",
        "tabelas": ["lista", "de", "tabelas"],
        "filtros": ["condicao1", "condicao2"],
        "agregacoes": ["funcao(coluna) AS alias"],
        "grupo_por": ["coluna1", "coluna2"],
        "ordenacao": ["coluna DESC/ASC"],
        "limite": 10,
        "formato_saida": "tabela/gráfico/texto"
    }}

    Exemplo para "Top 5 estados com mais vendas em 2024":
    {{
        "intencao": "Ranking dos 5 estados com maior volume de vendas em 2024",
        "tabelas": ["compras", "clientes"],
        "filtros": ["strftime('%Y', compras.data_compra) = '2024'"],
        "agregacoes": ["SUM(compras.valor) AS total_vendas", "COUNT(compras.id) AS total_pedidos"],
        "grupo_por": ["clientes.estado"],
        "ordenacao": ["total_vendas DESC"],
        "limite": 5,
        "formato_saida": "tabela"
    }}
    """
)

# Prompt para geração de SQL
SQL_PROMPT = PromptTemplate(
    input_variables=["interpretation"],
    template="""
    Você é um especialista em SQLite. Gere uma query SQL válida seguindo estas regras:

    ### Tabelas Disponíveis:
    - clientes(id, nome, email, idade, cidade, estado, profissao, genero)
    - compras(id, cliente_id, data_compra, valor, categoria, canal)
    - suporte(id, cliente_id, data_contato, tipo_contato, resolvido, canal)
    - campanhas_marketing(id, cliente_id, nome_campanha, data_envio, interagiu, canal)

    ### Relacionamentos (JOINs):
    - compras.cliente_id = clientes.id
    - suporte.cliente_id = clientes.id
    - campanhas_marketing.cliente_id = clientes.id

    ### Regras Importantes:
    1. Use INNER JOIN quando precisar de dados relacionados
    2. Use aliases para tabelas (c para clientes, co para compras, etc.)
    3. Para datas use: strftime('%Y', data_compra) = '2024'
    4. Para valores monetários use: ROUND(SUM(valor), 2)
    5. Para percentuais use: ROUND((COUNT(*) * 100.0 / total), 2)

    ### Interpretação da Solicitação:
    {interpretation}

    ### Instruções Finais:
    - Gere APENAS a query SQL válida
    - Sem explicações ou comentários
    - Use nomes descritivos para aliases
    - Inclua LIMIT quando especificado
    - Use ORDER BY quando há ordenação

    ### Exemplo de Query Esperada:
    SELECT 
        c.estado,
        SUM(co.valor) AS total_vendas,
        COUNT(co.id) AS total_pedidos
    FROM compras co
    INNER JOIN clientes c ON co.cliente_id = c.id
    WHERE strftime('%Y', co.data_compra) = '2024'
    GROUP BY c.estado
    ORDER BY total_vendas DESC
    LIMIT 5;
    """
)

# Prompt para formatação de respostas
FORMATTING_PROMPT = PromptTemplate(
    input_variables=["original_question", "query_results"],
    template="""
    Você é um analista de dados experiente. Formate os resultados para apresentação executiva.

    ### Pergunta Original:
    {original_question}

    ### Dados Obtidos (JSON):
    {query_results}

    ### Instruções de Formatação:
    1. **Resumo Executivo**: 1-2 frases com o principal insight
    2. **Dados Formatados**: 
       - Para tabelas: use Markdown com alinhamento
       - Para valores monetários: R$ X.XXX,XX
       - Para percentuais: XX,X%
       - Para números: formatação com separadores de milhares
    3. **Insights Chave**:
       - Destaque máximos, mínimos, médias
       - Identifique tendências ou padrões
       - Mencione outliers relevantes
    4. **Recomendações**: Se apropriado, sugira ações
    5. **Limite**: Máximo 250 palavras

    ### Formato por Tipo:
    - **Tabelas**: Use | Coluna | Valor | formato Markdown
    - **Gráficos**: Descreva o tipo ideal e principais pontos
    - **Métricas**: Destaque KPIs principais com contexto

    ### Exemplo para "Vendas por categoria":
    📊 **Resumo**: As vendas totalizaram R$ 45.230,00 distribuídas em 4 categorias principais.

    | Categoria | Vendas | Participação |
    |-----------|--------|--------------|
    | Eletrônicos | R$ 18.950,00 | 41,9% |
    | Roupas | R$ 12.340,00 | 27,3% |
    | Casa | R$ 8.760,00 | 19,4% |
    | Livros | R$ 5.180,00 | 11,4% |

    🎯 **Insights**: Eletrônicos dominam com 42% das vendas. Oportunidade de crescimento em Casa e Livros.
    """
)

# Prompt para tratamento de erros
ERROR_PROMPT = PromptTemplate(
    input_variables=["error_message", "query", "user_question"],
    template="""
    Você é um assistente técnico amigável. Explique o erro de forma clara e ofereça soluções.

    ### Pergunta do Usuário:
    {user_question}

    ### Erro Técnico:
    {error_message}

    ### Query que Falhou:
    {query}

    ### Instruções:
    1. **Tradução do Erro**: Explique em linguagem simples
    2. **Causa Provável**: Identifique o que pode ter causado
    3. **Soluções**: Sugira 2-3 alternativas práticas
    4. **Tom**: Profissional mas acessível
    5. **Limite**: Máximo 150 palavras

    ### Tipos Comuns de Erro:
    - **"no such table"**: Tabela não existe
    - **"no such column"**: Campo não encontrado
    - **"syntax error"**: Erro de SQL
    - **"ambiguous column"**: Campo duplicado entre tabelas

    ### Exemplo de Resposta:
    ❌ **Problema Identificado**: Não foi possível encontrar os dados solicitados.

    🔍 **Causa**: O campo 'vendas_totais' não existe na tabela. Os campos disponíveis são: valor, categoria, data_compra.

    💡 **Soluções**:
    1. Reformule a pergunta usando "valor" ao invés de "vendas"
    2. Tente: "Qual o total de valores por categoria?"
    3. Verifique se o período solicitado tem dados disponíveis

    🔧 Posso ajudar reformulando sua pergunta!
    """
)

# Prompt adicional para validação de dados
VALIDATION_PROMPT = PromptTemplate(
    input_variables=["query_results", "expected_format"],
    template="""
    Valide se os resultados da query estão no formato esperado e contêm dados válidos.

    ### Resultados Obtidos:
    {query_results}

    ### Formato Esperado:
    {expected_format}

    ### Verificações:
    1. Dados não estão vazios
    2. Tipos de dados corretos (números, datas, textos)
    3. Valores fazem sentido (sem negativos inesperados)
    4. Estrutura conforme esperado

    Retorne apenas: "VÁLIDO" ou "INVÁLIDO: [motivo]"
    """
)