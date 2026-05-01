# 📊 MSR: Impacto Sociotécnico e Centralidade na Latência de Code Review

![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MSR Research](https://img.shields.io/badge/research-MSR-orange)

## 📝 Sobre o Projeto
Este repositório hospeda um pipeline automatizado para **Mining Software Repositories (MSR)**. A pesquisa investiga a dinâmica social no GitHub, focando em como a **centralidade de grau** (reputação estrutural) e a **experiência técnica** do autor influenciam a velocidade de resposta e o escrutínio em revisões de código.

> **Hipótese 1:** Quanto mais central e bem conectado um desenvolvedor está na rede de co-revisão, mais rápido e suave tende a ser o processo de code review que ele recebe.<br>
> **Hipótese 2:** A centralidade na rede de co-revisão acelera significativamente o processo de review para desenvolvedores experientes, mas tem um efeito reduzido ou irrelevante para desenvolvedores novatos.<br>
> **Hipótese 3:** A assimetria de centralidade atua como um 'filtro de prioridade': quanto maior a distância estrutural em favor do revisor (revisor muito central e autor periférico), mais lento é o review. Já a assimetria inversa (autor 'estrela' e revisor periférico) funciona como um acelerador gravitacional.

---

## 🎯 Questões de Pesquisa (RQs)

*   **RQ1:** Qual é o impacto da centralidade do desenvolvedor na rede de co-revisão sobre o processo de code review recebido?
*   **RQ2:** Como a experiência do desenvolvedor modera o impacto da centralidade no tempo e no rigor de revisão?
*   **RQ3:** De que forma a assimetria de centralidade entre o autor do PR e o revisor principal modera o tempo até o primeiro comentário de revisão?

---

## 🧠 Fluxo do Pipeline
O projeto é dividido em 6 fases modulares, garantindo que a extração de dados seja resiliente e os cálculos estatísticos sejam precisos:

1.  **Discovery:** Localização de repositórios baseada em critérios de maturidade (Estrelas, PRs, Contribuidores)
2.  **Extraction:** Mineração de dados via GitHub GraphQL (Agnóstico a transporte: HTTP ou CLI)
3.  **Sanitization:** Limpeza de anomalias de API e remoção de "Micro-repositórios"
4.  **Modeling:** Construção de grafos de colaboração e cálculo de métricas de centralidade via `networkx`
5.  **Analytics:** Execução de testes estatísticos (Spearman, Mann-Whitney U) usando o padrão *Strategy*
6.  **Reporting:** Geração automática de boxplots, histogramas e tabelas de frequência.

---

## 📁 Estrutura de Pastas
```text
.
├── config.yaml               # Parâmetros de busca e filtros metodológicos
├── data/                     # Datasets brutos e analíticos (.csv)
├── reports/                  # Figuras e outputs estatísticos
├── requirements.txt          # Dependências do projeto
└── src/                      # Núcleo da aplicação
    ├── infrastructure/       # Camada de Dados
    │   ├── factories/        # Fábricas de instanciamento (DIP)
    │   ├── fetchers/         # Implementações HTTP e CLI
    │   └── graphql/          # Clients e queries (.graphql)
    ├── models/               # Entidades e Classificadores de Experiência
    ├── services/             # Lógica de Negócio e Pipeline
    │   └── strategies/       # Implementação modular das RQs
    └── utils/                # Utilitários de Suporte
        ├── config/           # Parsing de YAML
        ├── data/             # Manipulação de arquivos
        ├── filters/          # Regras de filtragem de dados
        └── [output/time]     # Formatação e cálculos temporais

```

----------

## 🚀 Como Executar

### 1. Preparação do Ambiente

Bash

```
# Criar ambiente virtual
python -m venv .venv

# Ativar Ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

```

### 2. Credenciais

Crie um arquivo `.env` na raiz do projeto:



```
GITHUB_TOKEN=seu_token_aqui

```

### 3. Execução

O sistema possui uma interface CLI amigável para rodar fases isoladas ou o pipeline completo:

Bash

```
python src/app.py

```

----------

## 🔧 Configurações Metodológicas

O arquivo `config.yaml` permite ajustar o rigor da pesquisa sem alterar o código:

-   `min_prs_per_repo`: Padrão sugerido de 200 para evitar _toy projects_.
    
-   `min_stars`: Filtro de popularidade.
    
-   `target_languages`: Lista de linguagens para análise multi-domínio.
    

----------

## 📌 Notas Técnicas

-   **Abstração:** A extração GraphQL utiliza uma interface comum, permitindo troca entre o `http_fetcher` (mais rápido) e o `cli_fetcher` (fallback de segurança).
    
-   **Tratamento Temporal:** Cálculos de latência ignoram finais de semana para não enviesar a performance dos revisores.
