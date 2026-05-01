from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class RepositoryFetcher(ABC):
    """
    Contrato Puro. Define O QUE o sistema espera de um Fetcher,
    sem saber COMO ele é implementado ou registrado.
    """
    
    @abstractmethod
    def fetch(self, query_string: str, max_repos: int = 500) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _execute_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass