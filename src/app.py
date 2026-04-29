import sys
from pathlib import Path

# Como o app.py está DENTRO de src, a raiz do projeto é um nível acima
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Imports atualizados com base na sua estrutura real
from src.services.ReviewDataExtractor import ReviewDataExtractor
from src.services.fetcher_factory import RepositoryFetcherFactory
from src.services.repository_manager import RepositoryManager
from services.graph_modeler import GraphModeler
from src.services.statistical_analyzer import StatisticalAnalyzer
from src.services.visualizer import DataVisualizer

def run_phase_1():
    print("\n" + "="*50)
    print(" FASE 1: DESCOBERTA E FILTRAGEM (REPOSITÓRIOS)")
    print("="*50)
    
    fetcher = RepositoryFetcherFactory.create('http')
    manager = RepositoryManager(fetcher)
    
    print("🚀 Iniciando Prova de Conceito (POC) - Fase 1: 500 Repositórios")
    poc_repos = manager.fetch_poc_repositories(repos_per_lang=100)
    
    manager.display_results(poc_repos)
    manager.save_consolidated_data(poc_repos, filename="poc_repos_merged_filter.csv")


def run_phase_2():
    print("\n" + "="*50)
    print(" FASE 2: EXTRAÇÃO DE PULL REQUESTS E INTERAÇÕES")
    print("="*50)
    
    print("🚀 Lendo dados de 'poc_repos_merged_filter.csv'...")
    extractor = ReviewDataExtractor()
    extractor.extract_prs_from_csv()

def run_phase_3():
    print("\n" + "="*60)
    print(" FASE 3: MODELAGEM DE GRAFOS E CENTRALIDADE")
    print("="*60)
    
    modeler = GraphModeler()
    modeler.build_and_calculate()

def run_phase_4():
    print("\n" + "="*60)
    print(" FASE 4: ANÁLISE ESTATÍSTICA (RQs)")
    print("="*60)
    
    analyzer = StatisticalAnalyzer()
    analyzer.run_analysis()

# Geração de gráficos analíticos
def run_phase_5():
    print("\n" + "="*60)
    print(" FASE 5: GERAÇÃO DE GRÁFICOS ANALÍTICOS")
    print("="*60)
    visualizer = DataVisualizer()
    visualizer.generate_analytical_plots()


def main():
    while True:
        print("\n🛠️  MENU DE EXECUÇÃO DA POC")
        print("1. Executar o pipeline completo (Fase 1 -> Fase 2 -> Fase 3 -> Fase 4 -> Fase 5)")
        print("2. Executar APENAS a Fase 1 (Coleta de Repositórios)")
        print("3. Executar APENAS a Fase 2 (Extração de PRs do CSV existente)")
        print("4. Executar APENAS a Fase 3 (Modelagem de Grafos e Centralidade)")
        print("5. Executar APENAS a Fase 4 (Análise Estatística)")
        print("6. Executar APENAS a Fase 5 (Geração de Gráficos Analíticos)")
        print("0. Sair")
        
        escolha = input("\nEscolha a opção desejada (0-6): ").strip()
        
        if escolha == '1':
            run_phase_1()
            run_phase_2()
            run_phase_3()
            run_phase_4()
            run_phase_5()
            break
        elif escolha == '2':
            run_phase_1()
            break
        elif escolha == '3':
            run_phase_2()
            break
        elif escolha == '4':
            run_phase_3()
            break
        elif escolha == '5':
            run_phase_4()
            break
        elif escolha == '6':
            run_phase_5()
            break
        elif escolha == '0':
            print("Saindo do programa...")
            sys.exit(0)
        else:
            print("❌ Opção inválida. Digite um número de 0 a 5.")

if __name__ == "__main__":
    main()