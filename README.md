# 🤖 Desafio Técnico – Automação com IA e Análise Operacional

Este projeto é um protótipo funcional desenvolvido para o processo seletivo de estágio em Automação com IA e Análise Operacional. A aplicação utiliza inteligência artificial e agentes para interpretar comandos em linguagem natural e gerar insights a partir de dados reais de clientes, compras, suporte e campanhas de marketing.

---

## 🚀 Instruções de Execução

### 1. Clone o repositório
```bash
git clone https://github.com/Filip3Owl/data-analysis-ai.git
cd data-analysis-ai
````

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
# Ativação no Windows:
.venv\Scripts\activate
# Ativação no macOS/Linux:
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o app

```bash
streamlit run app.py
```

---

## 🧠 Fluxo dos Agentes

O sistema possui um fluxo de agentes IA que recebem comandos do usuário, interpretam a intenção e executam ações com ferramentas específicas (como consultas SQL). Veja o diagrama abaixo:





---

## 💬 Exemplos de Consultas Testadas

* "Top 10 clientes por vendas."
* "Clientes por estado."
* "Vendas dos últimos 30 dias."
* "Distribuição de clientes por idade."

---

## 📊 Insights Extraídos dos Dados

* -
* -
* -
* -

---

## 💡 Sugestões de Melhorias e Extensões

* Integração com banco de dados em tempo real (PostgreSQL, BigQuery).
* Uso de embeddings para melhorar a compreensão semântica de consultas.

---

## 🧾 Estrutura do Projeto

```
.
├── app.py
├── README.md
├── requirements.txt
├── .flake8
├── .gitignore
├── data/
│   └── dados.db (ou equivalente)
├── pngs/
│   └── agents_flow.png
├── docs/
│   ├── relatorio_insights.md
│   └── sugestoes_melhorias.md
├── src/
│   ├── agents.py
│   ├── database.py
│   ├── prompts.py
│   └── utils.py
```

---

## 👨‍💻 Desenvolvido por

Filipe Rangel – Projeto para processo seletivo de estágio.

```

---
