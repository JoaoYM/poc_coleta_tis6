# src/infrastructure/fetchers/cli_repository_fetcher.py
import time
import subprocess
import json
from typing import Dict, Any, Optional
from src.infrastructure.fetchers.base_repository_fetcher import BaseRepositoryFetcher

class CliRepositoryFetcher(BaseRepositoryFetcher):
    def _execute_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cmd = ['gh', 'api', 'graphql', '-f', f'query={query}']
        if variables:
            cmd.extend(['-F', f'variables={json.dumps(variables)}'])

        max_retries = 5
        for attempt in range(max_retries):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return json.loads(result.stdout)
                
                error_msg = result.stderr.strip()
                if "502" in error_msg or "504" in error_msg or "timeout" in error_msg.lower():
                    wait = 2 * (2 ** attempt)
                    print(f"⏳ CLI Timeout detectado. Retentando em {wait}s...")
                    time.sleep(wait)
                else:
                    return {"errors": error_msg, "data": None}
            except Exception as e:
                wait = 2 * (2 ** attempt)
                print(f"🔌 Erro no subprocesso CLI: {e}. Retentando em {wait}s...")
                time.sleep(wait)

        return {"errors": "Excedeu limite de retentativas CLI.", "data": None}