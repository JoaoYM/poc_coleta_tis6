# src/infrastructure/fetchers/http_repository_fetcher.py
import time
import requests
from typing import Dict, Any, Optional
from src.infrastructure.fetchers.base_repository_fetcher import BaseRepositoryFetcher

class HttpRepositoryFetcher(BaseRepositoryFetcher):
    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.api_url = "https://api.github.com/graphql"

    def _execute_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url, json={"query": query, "variables": variables or {}},
                    headers=headers, timeout=20
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [502, 503, 504]:
                    wait = 2 * (2 ** attempt)
                    print(f"⏳ HTTP {response.status_code}. Retentando em {wait}s...")
                    time.sleep(wait)
                else:
                    return {"errors": f"HTTP {response.status_code}", "data": None}
            except requests.exceptions.RequestException as e:
                wait = 2 * (2 ** attempt)
                print(f"🔌 Falha de rede HTTP: {e}. Retentando em {wait}s...")
                time.sleep(wait)
                
        return {"errors": "Excedeu limite de retentativas HTTP.", "data": None}