from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv
import json
import time

from src.utils.output_formatter import RepositoryOutputFormatter


class RepositoryFetcher(ABC):
    
    @abstractmethod
    def fetch(self, pages: int = 100, save_json: bool = False, save_csv: bool = False) -> List[Dict[str, Any]]:
        pass
    
    def _standardize_repository(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": repo.get("name", "Unknown"),
            "url": repo.get("url", ""),
            "stargazerCount": repo.get("stargazerCount", 0),
            "createdAt": repo.get("createdAt", ""),
            "updatedAt": repo.get("updatedAt", ""),
            "releases_count": repo.get("releases_count", 0),
            "collectedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


class BaseRepositoryFetcher(RepositoryFetcher):
    """Base class that implements fetching logic common to all methods."""

    def __init__(self):
        self.output = RepositoryOutputFormatter()
        self.base_path = Path(__file__).resolve().parent.parent.parent

        self.query_file = (
            self.base_path / "src" / "infrastructure" / "graphql" / "query.graphql"
        )
        self.data_dir = self.base_path / "data"

    def _get_query_content(self) -> str:
        if not self.query_file.exists():
            raise FileNotFoundError(f"Arquivo de query não encontrado em: {self.query_file}")
        return self.query_file.read_text(encoding="utf-8")

    @abstractmethod
    def _execute_request(self, query: str, cursor: Optional[str]) -> Dict[str, Any]:
        """Each subclass implements its own communication mechanism."""
        pass

    def fetch(self, pages: int = 100, save_json: bool = False, save_csv: bool = False) -> List[Dict[str, Any]]:
        query_content = self._get_query_content()
        all_repos: List[Dict[str, Any]] = []
        cursor = None
        
        self.output.print_fetch_start(self.__class__.__name__, pages)

        # Utiliza o Context Manager do formatter para abstrair a UI
        with self.output.fetch_progress_context(pages) as ui_updater:

            for page in range(1, pages + 1):
                max_retries = 5
                data = None
                
                # Delega a atualização visual para o formatter
                ui_updater.update_status(page, pages)
                
                for attempt in range(1, max_retries + 1):
                    data = self._execute_request(query_content, cursor)

                    if data is None:
                        self.output.print_error(f"Resposta None (tentativa {attempt}/{max_retries})")
                        if attempt < max_retries:
                            time.sleep(2 ** attempt)
                            continue
                        break

                    if 'data' not in data or data.get('data') is None or data['data'].get('search') is None:
                        err = data.get('errors', 'Resposta malformada ou erro de permissão')
                        self.output.print_error(f"Erro na resposta (tentativa {attempt}/{max_retries}): {err}")
                        if attempt < max_retries:
                            time.sleep(2 ** attempt)
                            continue
                        break
                    # Success
                    break

                if data is None or 'data' not in data or data.get('data') is None or data['data'].get('search') is None:
                    self.output.print_error("Falha após todas as tentativas. Encerrando coleta.")
                    break

                search_results = data['data']['search']
                repos_this_page = []

                for edge in search_results.get('edges', []):
                    node = edge.get('node')
                    if not node: continue
                    
                    repo_data = self._parse_node(node)
                    
                    try:
                        standardized = self._standardize_repository(repo_data)
                        repos_this_page.append(standardized)
                        all_repos.append(standardized)
                    except Exception as e:
                        self.output.print_error(f"Erro ao padronizar repositório {repo_data.get('name')}: {e}")
                        continue

                # Notifica o formatador de que a página avançou com sucesso
                ui_updater.advance_success(len(all_repos))

                page_info = search_results.get('pageInfo', {})
                if not page_info.get('hasNextPage'):
                    break
                
                cursor = page_info.get('endCursor')
                time.sleep(0.5)

        if save_json:
            self._save_json(all_repos)
        if save_csv:
            self._save_csv(all_repos)
        return all_repos

    def _parse_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse node handling possible nulls from GraphQL."""
        return {
            "name": node.get('name', 'N/A'),
            "url": node.get('url', ''),
            "stargazerCount": node.get('stargazerCount', 0),
            "createdAt": node.get('createdAt', ''),
            "updatedAt": node.get('updatedAt', ''),
            "releases_count": (node.get('releases') or {}).get('totalCount', 0),
        }

    def _save_json(self, repos: List[Dict[str, Any]]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.data_dir / 'repos.json'
        output_file.write_text(json.dumps(repos, indent=2), encoding='utf-8')
        self.output.print_save_success(str(output_file))

    def _save_csv(self, repos: List[Dict[str, Any]]) -> None:
        if not repos:
            return
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.data_dir / 'repos.csv'
        fieldnames = list(repos[0].keys())
        with output_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(repos)
        self.output.print_save_success(str(output_file))