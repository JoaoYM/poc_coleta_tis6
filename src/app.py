import sys
import argparse
from pathlib import Path

# Configuração do PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Imports de Infraestrutura e Serviços
from src.infrastructure.factories.environment_resolver import EnvironmentResolver
from src.services.repository_manager import RepositoryManager
from src.services.review_data_extractor import ReviewDataExtractor
from src.services.data_cleaner import DataCleaner  # NOVO IMPORT
from src.services.graph_modeler import GraphModeler
from src.services.statistical_analyzer import StatisticalAnalyzer
from src.services.visualizer import DataVisualizer
from src.utils.config.config_manager import ConfigManager

# === NOVOS IMPORTS DA FASE 5 (PADRÃO STRATEGY) ===
from src.services.statistical_analyzer import StatisticalAnalyzer
from src.services.strategies.rq1_strategy import RQ1CentralityStrategy
from src.services.strategies.rq2_strategy import RQ2ExperienceStrategy
from src.services.strategies.rq3_strategy import RQ3AsymmetryStrategy

def setup_cli_arguments():
    """Configura e analisa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="MSR POC Data Pipeline")
    parser.add_argument(
        '--total-repos', 
        type=int, 
        help='Sobrescreve a quantidade total de repositórios a serem coletados na Fase 1.'
    )
    return parser.parse_args()

def run_phase_1():
    print("\n" + "="*50)
    print(" FASE 1: DESCOBERTA E FILTRAGEM (REPOSITÓRIOS)")
    print("="*50)
    
    config = ConfigManager()
    print(f"🎯 Meta definida: Coletar {config.target_total_repos} repositórios totais.")
    print(f"📈 Distribuição: {config.repos_per_language} repositórios por linguagem.")
    
    fetcher = EnvironmentResolver.auto_detect_and_create()
    manager = RepositoryManager(fetcher)
    
    poc_repos = manager.fetch_poc_repositories() # Não passa mais parâmetros aqui
    
    manager.display_results(poc_repos)
    manager.save_consolidated_data(poc_repos, base_filename="poc_repos_merged_filter")

def run_phase_2():
    print("\n" + "="*50)
    print(" FASE 2: EXTRAÇÃO DE PULL REQUESTS E INTERAÇÕES")
    print("="*50)
    
    print("🚀 Preparando motor de extração...")
    # Auto-detecta HTTP ou CLI para a Fase 2 também
    fetcher = EnvironmentResolver.auto_detect_and_create()
    extractor = ReviewDataExtractor(fetcher)
    extractor.extract_prs_from_csv()


def run_phase_3():
    print("\n" + "="*50)
    print(" FASE 3: SANITIZAÇÃO DE DADOS (DATA CLEANING)")
    print("="*50)
    
    cleaner = DataCleaner()
    cleaner.sanitize_extracted_data()


def run_phase_4():
    print("\n" + "="*60)
    print(" FASE 4: MODELAGEM DE GRAFOS E CENTRALIDADE")
    print("="*60)
    
    modeler = GraphModeler()
    # Importante: Garanta que o GraphModeler esteja lendo 'poc_prs_sanitized.csv' internamente!
    modeler.build_and_calculate()


def run_phase_5():
    print("\n" + "="*60)
    print(" FASE 5: ANÁLISE ESTATÍSTICA (RQs)")
    print("="*60)
    
    # 1. Instancia as estratégias fatiadas
    strategies = [
        RQ1CentralityStrategy(),
        RQ2ExperienceStrategy(),
        RQ3AsymmetryStrategy()
    ]
    
    # 2. Injeta a lista de estratégias no Orquestrador
    analyzer = StatisticalAnalyzer(strategies=strategies)
    
    # 3. Manda rodar! O Orquestrador cuida do CSV e delega a matemática pras estratégias
    analyzer.run_analysis()


def run_phase_6():
    print("\n" + "="*60)
    print(" FASE 6: GERAÇÃO DE GRÁFICOS ANALÍTICOS")
    print("="*60)
    
    visualizer = DataVisualizer()
    visualizer.generate_analytical_plots()


def main():
    # 1. Lê a configuração do CLI
    args = setup_cli_arguments()
    
    # 2. Inicializa o ConfigManager e aplica o override se existir
    config = ConfigManager()
    if args.total_repos:
        config.set_total_repos_override(args.total_repos)
        print(f"⚙️  [CLI OVERRIDE] Total de repositórios ajustado para: {config.target_total_repos}")

    while True:
        print(f"\n🛠️  MENU DE EXECUÇÃO DA POC (Meta Atual: {config.target_total_repos} Repos)")
        print("1. Executar o pipeline completo (Fases 1 a 6)")
        print("2. Executar APENAS a Fase 1 (Coleta de Repositórios)")
        print("3. Executar APENAS a Fase 2 (Extração de PRs do CSV existente)")
        print("4. Executar APENAS a Fase 3 (Sanitização e Limpeza)")
        print("5. Executar APENAS a Fase 4 (Modelagem de Grafos e Centralidade)")
        print("6. Executar APENAS a Fase 5 (Análise Estatística)")
        print("7. Executar APENAS a Fase 6 (Geração de Gráficos)")
        print("0. Sair")
        
        escolha = input("\nEscolha a opção desejada (0-7): ").strip()
        
        if escolha == '1':
            run_phase_1()
            run_phase_2()
            run_phase_3()
            run_phase_4()
            run_phase_5()
            run_phase_6()
            break
        elif escolha == '2': run_phase_1(); break
        elif escolha == '3': run_phase_2(); break
        elif escolha == '4': run_phase_3(); break
        elif escolha == '5': run_phase_4(); break
        elif escolha == '6': run_phase_5(); break
        elif escolha == '7': run_phase_6(); break
        elif escolha == '0':
            print("Saindo do programa...")
            sys.exit(0)
        else:
            print("❌ Opção inválida. Digite um número de 0 a 7.")

if __name__ == "__main__":
    main()