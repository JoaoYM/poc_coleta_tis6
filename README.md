# 📊 MSR: Impacto Sociotécnico e Centralidade na Latência de Code Review

## 📝 Sobre o Projeto
Este repositório contém o pipeline de mineração, extração, sanitização e análise estatística para uma pesquisa empírica em **Mining Software Repositories (MSR)**.

O objetivo é investigar como a posição social de um desenvolvedor na comunidade (centralidade de grau) e a experiência técnica moderam o tempo até a primeira revisão de Pull Request.

## 🎯 Questões de Pesquisa
* **RQ1:** Qual é o impacto da centralidade de grau do autor no tempo de resposta da primeira revisão?
* **RQ2:** Como a experiência do autor (novato vs experiente) modera o efeito da centralidade na latência de revisão?
* **RQ3:** Como a desigualdade de centralidade entre autor e revisor afeta a velocidade de revisão?

## 🧠 Arquitetura do Pipeline
O projeto está organizado em um pipeline modular com as fases:
1. Coleta de repositórios
2. Extração de Pull Requests
3. Limpeza de dados
4. Modelagem de grafos
5. Análise estatística
6. Geração de relatórios e gráficos

## 📁 Estrutura do Projeto
```text
├── .venv/                        # Ambiente virtual Python
├── config.yaml                   # Configurações de coleta e filtros
├── data/                         # Dados CSV coletados e processados
├── reports/                      # Gráficos e relatórios gerados
├── requirements.txt              # Dependências Python
├── README.md                     # Documentação do projeto
└── src/                          # Código fonte da aplicação
    ├── app.py                    # Ponto de entrada CLI
    ├── infrastructure/           # Fetchers, GraphQL e fábricas
    ├── models/                   # Entidades de domínio
    ├── services/                 # Pipeline e lógica de análise
    └── utils/                    # Utilitários de configuração e formatação
```

## 🚀 Como Executar
1. Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure o token do GitHub em `.env`:

```text
GITHUB_TOKEN=seu_token_aqui
```

3. Execute o aplicativo:

```powershell
python src/app.py
```

## 🔧 Configuração
A coleta usa `config.yaml` para definir:
* `target_total_repos`
* `target_languages`
* critérios de busca
* limites de PRs e contribuidores

## 📌 Observações
* O modo HTTP usa `GITHUB_TOKEN`.
* O modo CLI usa `gh api` como alternativa.
* A extração GraphQL é agnóstica ao transporte e funciona com qualquer fetcher suportado.
