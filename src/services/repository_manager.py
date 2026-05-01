from typing import List, Dict, Any
from src.infrastructure.fetchers.contract.repository_fetcher import RepositoryFetcher
from src.utils.output.output_formatter import RepositoryOutputFormatter
from src.utils.data.data_exporter import DataExporter
from src.utils.config.config_manager import ConfigManager # Novo Import

class RepositoryManager:
    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher
        self.output = RepositoryOutputFormatter()
        self.exporter = DataExporter()
        self.config = ConfigManager() # Inicializa o Singleton
    
    def fetch_poc_repositories(self) -> List[Dict[str, Any]]:
        """
        Coordena a coleta usando os parâmetros centralizados no config.yaml.
        """
        all_collected_repos = []
        
        # Lê os parâmetros direto da configuração
        target_languages = self.config.target_languages
        base_criteria = self.config.base_criteria
        repos_per_lang = self.config.repos_per_language
        
        for lang in target_languages:
            query_string = f"language:{lang} {base_criteria}"
            print(f"\n🔍 Buscando {repos_per_lang} repositórios para a linguagem: [bold]{lang}[/bold]")
            
            repos = self.fetcher.fetch(
                query_string=query_string, 
                max_repos=repos_per_lang
            )
            all_collected_repos.extend(repos)
            
        return all_collected_repos
    
    def display_results(self, repos: List[Dict[str, Any]]) -> None:
        """
        Renderiza as tabelas bonitas no terminal usando o 'rich'.
        """
        if not repos:
            self.output.print_no_repos()
            return
        
        self.output.print_repositories(repos)
        self.output.print_summary(repos)
        self.output.print_completion(len(repos))
    
    def save_consolidated_data(self, repos: List[Dict[str, Any]], base_filename: str = "poc_repos"):
        """
        Delega o salvamento dos dados para o Exporter em múltiplos formatos.
        """
        if not repos:
            return
        
        # O Manager não sabe mais onde fica a pasta 'data' nem como um CSV é escrito.
        # Ele apenas manda o Exporter trabalhar:
        self.exporter.save_csv(repos, f"{base_filename}.csv")
        self.exporter.save_json(repos, f"{base_filename}.json")