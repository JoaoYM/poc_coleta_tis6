from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from src.infrastructure.fetchers.contract.repository_fetcher import RepositoryFetcher
from src.utils.output.output_formatter import RepositoryOutputFormatter

class BaseRepositoryFetcher(RepositoryFetcher):
    """
    Classe Base de Infraestrutura (Template Method).
    Implementa a lógica comum de paginação, sanitização e padronização (DRY).
    Gerencia o Auto-Registro Dinâmico (Plugin Pattern) das subclasses concretas.
    """
    
    # Dicionário dinâmico que registra automaticamente os fetchers concretos
    _registry: Dict[str, Any] = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Auto-descobre os fetchers que herdam desta classe na pasta infrastructure."""
        super().__init_subclass__(**kwargs)
        # Extrai o prefixo do nome da classe (ex: HttpRepositoryFetcher -> 'http')
        method_name = cls.__name__.replace('RepositoryFetcher', '').lower()
        if method_name != 'base':
            cls._registry[method_name] = cls

    def __init__(self):
        self.output = RepositoryOutputFormatter()
        self.base_path = Path(__file__).resolve().parent.parent.parent.parent
        self.query_file = self.base_path / "src" / "infrastructure" / "graphql" / "query.graphql"

    def _get_query_content(self) -> str:
        """Lê o arquivo de query GraphQL do disco."""
        if not self.query_file.exists():
            raise FileNotFoundError(f"Arquivo de query não encontrado em: {self.query_file}")
        return self.query_file.read_text(encoding="utf-8")

    @abstractmethod
    def _execute_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Contrato que obriga a subclasse (HTTP ou CLI) a implementar a comunicação.
        A subclasse DEVE gerenciar seu próprio Backoff Exponencial e Timeout aqui dentro,
        retornando apenas os dados de sucesso ou um dicionário com a chave 'errors'.
        """
        pass

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa a mesma query GraphQL usando o transporte da subclasse."""
        return self._execute_request(query, variables)

    def fetch(self, query_string: str, max_repos: int = 500) -> List[Dict[str, Any]]:
        """
        Template Method: Orquestra a paginação da API do GitHub e a padronização dos dados. 
        Delega a chamada de rede para as subclasses via _execute_request.
        """
        query_content = self._get_query_content()
        all_repos: List[Dict[str, Any]] = []
        cursor = None
        
        # O GitHub GraphQL retorna no máximo 100 por página, mas definimos 10 na query.
        estimated_pages = (max_repos // 10) + (1 if max_repos % 10 > 0 else 0)
        
        self.output.print_fetch_start(self.__class__.__name__, estimated_pages, max_repos)

        # Utiliza o Context Manager do formatter para abstrair a UI
        with self.output.fetch_progress_context(estimated_pages) as ui_updater:
            page = 1
            while len(all_repos) < max_repos:
                ui_updater.update_status(page, estimated_pages)
                
                variables = {
                    "queryString": query_string,
                    "cursor": cursor
                }
                
                # A classe base não sabe COMO os dados vêm. Ela delega a chamada.
                # Como o loop de retry está na subclasse, se chegar um erro aqui, é erro fatal.
                data = self._execute_request(query_content, variables)

                if data is None or 'errors' in data or 'data' not in data or data.get('data') is None:
                    err = data.get('errors', 'Falha definitiva após todas as tentativas da subclasse.') if data else 'Resposta None'
                    self.output.print_error(f"Encerrando coleta na página {page}: {err}")
                    break

                search_results = data['data'].get('search')
                if not search_results:
                    self.output.print_error("Nenhum resultado encontrado na busca do GraphQL.")
                    break

                # Processamento dos repositórios retornados na página
                for edge in search_results.get('edges', []):
                    node = edge.get('node')
                    if not node: 
                        continue
                    
                    # Extrai as variáveis base
                    repo_data = self._parse_node(node)
                    
                    try:
                        # Padroniza e insere metadados (como o collectedAt)
                        standardized = self._standardize_repository(repo_data)
                        
                        # Filtro de sanidade local
                        if standardized['total_prs'] >= 1000 and standardized['contributor_count'] >= 50:
                            all_repos.append(standardized)
                            
                        # Se já atingiu o limite solicitado, para de adicionar
                        if len(all_repos) >= max_repos:
                            break
                            
                    except Exception as e:
                        self.output.print_error(f"Erro ao padronizar repositório {repo_data.get('name')}: {e}")
                        continue

                # Notifica o formatador de que a página avançou com sucesso
                ui_updater.advance_success(len(all_repos))

                if len(all_repos) >= max_repos:
                    break

                # Lógica de Paginação (Cursor)
                page_info = search_results.get('pageInfo', {})
                if not page_info.get('hasNextPage'):
                    break
                
                cursor = page_info.get('endCursor')
                page += 1
                
                # Pequeno respiro entre páginas de sucesso (opcional)
                time.sleep(0.5)

        return all_repos

    def _parse_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai os dados brutos do nó retornado pelo GraphQL."""
        return {
            "name": node.get('nameWithOwner', 'N/A'),
            "url": node.get('url', ''),
            "stargazerCount": node.get('stargazerCount', 0),
            "createdAt": node.get('createdAt', ''),
            "pushedAt": node.get('pushedAt', ''),
            "total_prs": (node.get('pullRequests') or {}).get('totalCount', 0),
            "contributor_count": (node.get('mentionableUsers') or {}).get('totalCount', 0),
        }

    def _standardize_repository(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica os metadados de coleta e garante a estrutura dos dados."""
        return {
            "name": repo.get("name", "Unknown"),
            "url": repo.get("url", ""),
            "stargazerCount": repo.get("stargazerCount", 0),
            "createdAt": repo.get("createdAt", ""),
            "pushedAt": repo.get("pushedAt", ""),
            "total_prs": repo.get("total_prs", 0),
            "contributor_count": repo.get("contributor_count", 0),
            "collectedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }