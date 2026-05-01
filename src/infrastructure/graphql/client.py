import time
from typing import Dict, Any, Optional

class GraphQLClient:
    """
    Adaptador GraphQL agnóstico ao transporte.
    Recebe um fetcher HTTP/CLI e delega a execução da query para ele.
    """
    def __init__(self, fetcher):
        self.fetcher = fetcher

    def execute(self, query: str, variables: Dict[str, Any], max_attempts: int = 5, base_wait: int = 3) -> Optional[Dict[str, Any]]:
        for attempt in range(max_attempts):
            data = self.fetcher.execute(query, variables)
            if data is None:
                wait_time = base_wait * (2 ** attempt)
                print(f"⏳ Falha GraphQL detectada. Tentativa {attempt+1}/{max_attempts}. Aguardando {wait_time}s...")
                time.sleep(wait_time)
                continue

            if isinstance(data, dict) and 'errors' in data:
                print(f"❌ Erro GraphQL: {data['errors']}")
                return None

            return data

        return None