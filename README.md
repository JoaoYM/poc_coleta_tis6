# 📊 MSR: Impacto Sociotécnico e Centralidade na Latência de Code Review

## 📝 Sobre o Projeto
Este repositório contém o pipeline de mineração, extração, sanitização e análise estatística para uma pesquisa empírica na área de **Mining Software Repositories (MSR)**. 

O objetivo principal do estudo é investigar como a posição social de um desenvolvedor na comunidade (Centralidade de Grau em um grafo de revisões) e a sua experiência técnica moderam a **latência (tempo de espera)** para a primeira revisão formal de um Pull Request (PR) em ecossistemas Open Source.

### 🎯 Questões de Pesquisa (RQs)
* **RQ1:** Qual o impacto da centralidade de grau do autor do PR no tempo de resposta para a primeira revisão?
* **RQ2:** Como a experiência prévia do autor (novato vs. experiente) modera o efeito da centralidade na latência de revisão?
* **RQ3:** Como a assimetria estrutural (diferença de status de centralidade entre autor e revisor) afeta a velocidade da revisão?

## 🧠 Arquitetura Metodológica (Data Pipeline)
O projeto foi estruturado em um pipeline modular de 5 fases, garantindo reprodutibilidade e resiliência:

### Fase 1: Descoberta (Filtragem REST)
Busca por repositórios maduros e ativos para evitar "projetos de brinquedo" ou abandonados:
* **Critérios:** `>= 1000 stars`, criados antes de `Março/2023` (prevenção de *Left-Censoring*) e com *push* recente após `Outubro/2025`.

### Fase 2: Extração Cirúrgica (GraphQL)
Extração exclusiva de PRs efetivamente mesclados (`is:merged -is:draft`) em uma janela de coleta focada (Jan-Fev de 2026) para evitar viés temporal (*Concept Drift*).
* **Cálculo de Latência (Business Hours):** Implementado filtro com `numpy` para subtrair finais de semana da latência, isolando o tempo em horas úteis.
* **Matriz de Experiência (Time Decay):** Criação de um perfil sociotécnico cacheado avaliando o histórico do desenvolvedor nos últimos **24 meses** anteriores à abertura do PR. Avalia: Volume (PRs anteriores), Track Record (Taxa de aceitação) e Impacto Formal (Uso de `APPROVED` / `CHANGES_REQUESTED`).

### Fase 2.5: Sanitização (Data Cleaning)
Remoção de ruídos acadêmicos do dataset:
* Exclusão de repositórios com baixa densidade (`< 10 PRs válidos`) que inviabilizariam a construção de um grafo social.
* Tratamento de falhas de timeout da API (falsos novatos).

### Fase 3: Modelagem de Grafos (NetworkX)
Mapeamento da rede direcionada (Revisor -> Autor) por repositório.
* Classificação relativa intra-comunidade via quantis empíricos: **Core (Top 15%)**, **Regular (P50 a P84)** e **Periférico (Bottom 50%)**.

### Fase 4 e 5: Análise Estatística e Visualização
Testes não-paramétricos aplicados a uma amostra final superior a **18.000 PRs**:
* **Correlação de Spearman** e **Mann-Whitney U** com cálculo de Effect Size (Cohen's d).
* Geração de gráficos de distribuição complexos (*Split Violin Plots* e *Boxplots*) controlando *outliers* com `seaborn`.

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.10+
* **Coleta e API:** GitHub GraphQL API, `requests` (com sistema de Checkpoints e Resiliência de Rede)
* **Estrutura de Dados:** `pandas`, `dataclasses`
* **Redes Complexas:** `networkx`
* **Estatística:** `scipy.stats`, `numpy`
* **Visualização:** `matplotlib`, `seaborn`

## 📁 Estrutura do Repositório

```text
├── .venv/                      # Ambiente virtual Python
├── data/                       # Datasets CSV (brutos, sanitizados e analíticos)
├── docs/                       # Documentações adicionais
├── reports/                    # Relatórios e gráficos gerados (.png, .pdf)
├── src/                        # Código fonte da aplicação
│   ├── infrastructure/         # Camada de comunicação externa
│   │   ├── factories/          # Padrão Factory para instanciar fetchers
│   │   ├── fetchers/           # Implementações de coleta (REST)
│   │   ├── graphql/            # Queries .graphql otimizadas
│   │   └── interfaces/         # Contratos e abstrações
│   ├── models/                 # Estruturas de domínio (ex: ExperienceProfile)
│   ├── services/               # Lógica de negócio e orquestração do pipeline
│   │   ├── data_cleaner.py     # Sanitização e filtro de anomalias
│   │   ├── graph_modeler.py    # Construção de grafos e cálculo de centralidade
│   │   ├── repository_manager.py
│   │   ├── ReviewDataExtractor.py # Motor principal de extração via GraphQL
│   │   ├── statistical_analyzer.py# Testes estatísticos
│   │   └── visualizer.py       # Geração de Boxplots e Violin Plots
│   ├── utils/                  # Formatadores de output no terminal
│   └── app.py                  # CLI interativo (Ponto de entrada do sistema)
├── .env.example                # Template de credenciais
├── .gitignore
├── README.md
└── requirements.txt            # Dependências Python

```

## 🚀 Como Executar o Projeto

### 1. Configuração do Ambiente e Credenciais

Clone o repositório, crie um ambiente virtual e instale as dependências:

Bash

```
git clone https://github.com/JoaoYM/poc_coleta_tis6
cd poc_coleta_tis6
python -m venv .venv

# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt

```

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example` e adicione o seu token de acesso pessoal do GitHub:

Snippet de código

```
GITHUB_TOKEN=ghp_seutokendogithubaqui

```

### 2. Execução do Pipeline CLI

O projeto possui um menu interativo executado através do `app.py`. Inicie o programa:

Bash

```
python src/app.py

```

Siga a ordem lógica do menu de extração:

1.  **[Fase 1]** Buscar repositórios relevantes via REST.
    
2.  **[Fase 2]** Extrair Pull Requests e Perfis via GraphQL (Suporta interrupções e retoma do disco).
    
3.  **[Fase 2.5]** Limpar e sanitizar os dados extraídos.
    
4.  **[Fase 3]** Modelar os Grafos Sociais e classificar Desenvolvedores (NetworkX).
    
5.  **[Fase 4 e 5]** Rodar testes estatísticos e exportar os gráficos em alta resolução para a pasta `reports/`.