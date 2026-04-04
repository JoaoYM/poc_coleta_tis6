import sys
from src.services.fetcher_factory import RepositoryFetcherFactory
from src.services.repository_manager import RepositoryManager
from src.utils.output_formatter import RepositoryOutputFormatter
from src.services.metrics_collector import MetricsCollector

def display_menu(options: list):
    print("=" * 60)
    print(" 🚀 LABORATÓRIO 02 - COLETOR DE MÉTRICAS (JAVA) ")
    print("=" * 60)
    print("\nEscolha uma opção:")
    
    # Lista dinamicamente as opções de coleta de dados
    for i, method in enumerate(options, 1):
        label = "🐙 Coletar Top 1.000 Repositórios (GitHub CLI)" if method == 'cli' else "🌐 Coletar Top 1.000 Repositórios (API Direta)"
        print(f"  [{i}] {label}")
    
    # Atualizado para refletir o processamento em lote do Lab02S02
    next_opt = len(options) + 1
    print(f"  [{next_opt}] ⚙️  Executar Extração CK em Lote (1.000 Repositórios - Lab02S02)")
    
    print("\n  [0] Sair")
    print("-" * 60)

def run_collection(method: str, save_json: bool, save_csv: bool):
    """Encapsulates execution to keep main loop clean"""
    try:
        print("\n" + "=" * 40)
        print(f"Iniciando coleta via {method.upper()}...")
        print("=" * 40 + "\n")
        
        fetcher = RepositoryFetcherFactory.create(method)
        manager = RepositoryManager(fetcher)
        
        repos = manager.fetch_repositories(pages=100, save_json=save_json, save_csv=save_csv)
        manager.display_results(repos)
        
    except Exception as e:
        RepositoryOutputFormatter.print_error(f"Erro na execução: {e}")

def run_ck_analysis():
    """Executa o script de clone, coleta do CK e sumarização (Lote)"""
    try:
        print("\n" + "=" * 40)
        print("Iniciando Automação de Clone e Extração de Métricas (Em Lote)...")
        print("=" * 40 + "\n")
        
        collector = MetricsCollector()
        # Chamada atualizada para o método de processamento em lote
        collector.process_all_repositories()
        
    except Exception as e:
        RepositoryOutputFormatter.print_error(f"Erro ao executar a automação: {e}")

def main(save_json=False, save_csv=False):
    # Obtém os métodos de coleta disponíveis na Factory
    available_methods = RepositoryFetcherFactory.get_available_methods()
    ck_option = str(len(available_methods) + 1)
    
    while True:
        display_menu(available_methods)
        choice = input("\n👉 Digite a opção: ").strip()

        if choice == '0':
            print("\n👋 Encerrando. Até logo!")
            break
            
        # Verifica se escolheu um método de coleta
        if choice.isdigit() and 1 <= int(choice) <= len(available_methods):
            selected_method = available_methods[int(choice) - 1]
            run_collection(selected_method, save_json, save_csv)
        
        # Verifica se escolheu a extração em lote do CK
        elif choice == ck_option:
            run_ck_analysis()
            
        else:
            print(f"\n❌ Opção inválida! Digite de 1 a {ck_option} ou 0.")

if __name__ == "__main__":
    should_save_json = "--json" in sys.argv
    should_save_csv = "--csv" in sys.argv
    try:
        # Por padrão, mantemos save_csv=True pois precisamos do arquivo para a base do lote
        main(save_json=should_save_json, save_csv=True)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompido pelo usuário. Saindo...")
        sys.exit(0)