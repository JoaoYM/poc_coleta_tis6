import os
from pathlib import Path
from dotenv import load_dotenv
from src.infrastructure.factories.repository_fetcher import RepositoryFetcherFactory

class EnvironmentResolver:
    """
    Isola a lógica de leitura do ambiente (.env) e decide qual estratégia
    de extração (Fetcher) deve ser utilizada pela fábrica.
    """
    
    @classmethod
    def auto_detect_and_create(cls):
        # Resolve o caminho dinamicamente para o .env na raiz do projeto
        env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        token = os.getenv("GITHUB_TOKEN")
        
        if token:
            print("🔐 [.env detectado] Inicializando HTTP Fetcher com Token Privado.")
            # Se o token existe, pede para a fábrica criar o HTTP passando o token
            return RepositoryFetcherFactory.create('http', token=token)
        else:
            print("⚡ [.env ausente] Fallback para CLI Fetcher (gh api).")
            print("   Certifique-se de estar autenticado via 'gh auth login' no terminal.")
            # Se não tem token, pede para a fábrica criar o CLI (que usa a sessão do SO)
            return RepositoryFetcherFactory.create('cli')