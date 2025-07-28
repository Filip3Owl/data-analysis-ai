from langchain.prompts import PromptTemplate

# Prompt para interpretação das perguntas
INTERPRETATION_PROMPT = PromptTemplate(
    input_variables=["user_input"],
    template="""
   Você é um especialista em SQL e análise de dados. Converta a solicitação do usuário em uma estrutura JSON usando APENAS estas tabelas:

    ### 📊 Estrutura do Banco de Dados:


    - sqlite_sequence
    - clientes
    - compras
    - suporte
    - campanhas_marketing

    Estrutura da tabela 'clientes':
    Colunas:
    - id: INTEGER PRIMARY KEY
    - nome: TEXT
    - email: TEXT
    - idade: INTEGER
    - cidade: TEXT
    - estado: TEXT
    - profissao: TEXT
    - genero: TEXT

    Estrutura da tabela 'compras':
    Colunas:
    - id: INTEGER PRIMARY KEY
    - cliente_id: INTEGER
    - data_compra: TEXT
    - valor: REAL
    - categoria: TEXT
    - canal: TEXT

    Estrutura da tabela 'suporte':
    Colunas:
    - id: INTEGER PRIMARY KEY
    - cliente_id: INTEGER
    - data_contato: TEXT
    - tipo_contato: TEXT
    - resolvido: BOOLEAN
    - canal: TEXT

    Estrutura da tabela 'campanhas_marketing':
    Colunas:
    - id: INTEGER PRIMARY KEY
    - cliente_id: INTEGER
    - nome_campanha: TEXT
    - data_envio: TEXT
    - interagiu: BOOLEAN
    - canal: TEXT

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

    ### Tabelas Disponíveis e Estrutura:
    1. clientes (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        email TEXT,
        idade INTEGER,
        cidade TEXT,
        estado TEXT,
        profissao TEXT,
        genero TEXT
    )

    2. compras (
        id INTEGER PRIMARY KEY,
        cliente_id INTEGER,
        data_compra TEXT (formato ISO: YYYY-MM-DD),
        valor REAL,
        categoria TEXT,
        canal TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )

    3. suporte (
        id INTEGER PRIMARY KEY,
        cliente_id INTEGER,
        data_contato TEXT (formato ISO: YYYY-MM-DD),
        tipo_contato TEXT,
        resolvido BOOLEAN,
        canal TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )

    4. campanhas_marketing (
        id INTEGER PRIMARY KEY,
        cliente_id INTEGER,
        nome_campanha TEXT,
        data_envio TEXT (formato ISO: YYYY-MM-DD),
        interagiu BOOLEAN,
        canal TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )

    ### Convenções de Aliases:
    - clientes → c
    - compras → co
    - suporte → s
    - campanhas_marketing → cm

    Tabela 'compras':
    → Coluna 'cliente_id' referencia:
     Tabela: 'clientes'
     Coluna: 'id'
     On Update: NO ACTION
     On Delete: NO ACTION
     ----------------------------------------

    Tabela 'suporte':
    → Coluna 'cliente_id' referencia:
        Tabela: 'clientes'
        Coluna: 'id'
        On Update: NO ACTION
        On Delete: NO ACTION
    ----------------------------------------

    Tabela 'campanhas_marketing':
    → Coluna 'cliente_id' referencia:
        Tabela: 'clientes'
        Coluna: 'id'
        On Update: NO ACTION
        On Delete: NO ACTION
    ----------------------------------------

TESTANDO INTEGRIDADE DOS RELACIONAMENTOS:
Chaves estrangeiras habilitadas: Não

    ### Regras SQL Importantes:
    1. Use INNER JOIN para combinar tabelas relacionadas (a menos que precise de LEFT JOIN)
    2. Sempre use aliases para tabelas
    3. Para datas:
       - Filtrar por ano: strftime('%Y', campo_data) = '2024'
       - Filtrar por mês: strftime('%m', campo_data) = '03'
       - Intervalo: campo_data BETWEEN '2024-01-01' AND '2024-12-31'
    4. Para valores monetários:
       - Soma: ROUND(SUM(valor), 2) AS total
       - Média: ROUND(AVG(valor), 2) AS media
    5. Para booleanos (resolvido/interagiu):
       - TRUE: resolvido = 1
       - FALSE: resolvido = 0
    6. Para percentuais:
       - ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tabela)), 2) AS percentual
    7. Para contagens distintas:
       - COUNT(DISTINCT campo) AS total_distinto
    8. Para texto:
       - Busca parcial: campo LIKE '%termo%'
       - Case insensitive: LOWER(campo) = LOWER('valor')

    ### Interpretação da Solicitação:
    {interpretation}

    ### Instruções Finais:
    - Gere APENAS a query SQL válida, sem explicações ou comentários
    - Use os aliases convencionados
    - Inclua LIMIT quando especificado
    - Use ORDER BY para ordenações
    - Adicione GROUP BY para agregações
    - Prefira CTEs (WITH) para consultas complexas
    - Formate o SQL para legibilidade

    ### Exemplo Completo:
    WITH clientes_ativos AS (
        SELECT c.id, c.nome, c.estado
        FROM clientes c
        INNER JOIN compras co ON c.id = co.cliente_id
        WHERE strftime('%Y', co.data_compra) = '2024'
        GROUP BY c.id
        HAVING COUNT(co.id) >= 3
    )
    SELECT
        ca.estado,
        COUNT(DISTINCT ca.id) AS total_clientes,
        ROUND(SUM(co.valor), 2) AS total_vendas,
        ROUND(SUM(co.valor) / COUNT(DISTINCT ca.id), 2) AS ticket_medio
    FROM clientes_ativos ca
    INNER JOIN compras co ON ca.id = co.cliente_id
    GROUP BY ca.estado
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
