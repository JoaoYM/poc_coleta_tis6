from typing import Any
from src.infrastructure.fetchers.base_repository_fetcher import BaseRepositoryFetcher

# IMPORTANTE: Importar a pasta fetchers garante que as subclasses (Http, Cli)
# sejam lidas pelo Python e acionem o __init_subclass__ da Base.
import src.infrastructure.fetchers 

class RepositoryFetcherFactory:
    """
    Fábrica Dinâmica. Instancia objetos consumindo o registro 
    construído pela BaseRepositoryFetcher.
    """
    
    @classmethod
    def create(cls, method: str, **kwargs: Any) -> BaseRepositoryFetcher:
        # Consulta o caderninho da classe Base
        fetcher_class = BaseRepositoryFetcher._registry.get(method.lower())
        
        if not fetcher_class:
            available = cls.get_available_methods()
            raise ValueError(f"❌ Método '{method}' não suportado. Escolha entre: {available}")
            
        # Instancia a classe passando as dependências dinâmicas (ex: token)
        return fetcher_class(**kwargs)

    @classmethod
    def get_available_methods(cls):
        return list(BaseRepositoryFetcher._registry.keys())