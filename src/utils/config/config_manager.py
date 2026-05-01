import yaml
from pathlib import Path
from typing import List, Dict, Any

class ConfigManager:
    """
    Gerencia a configuração global da pesquisa.
    Lê os parâmetros do config.yaml e aplica eventuais overrides do terminal.
    """
    _instance = None

    def __new__(cls):
        # Implementa o padrão Singleton para carregar a configuração apenas uma vez
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent.parent
        self.config_file = self.base_path / "config.yaml"
        
        self.config_data: Dict[str, Any] = {}
        
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f) or {}
        else:
            print(f"⚠️ Aviso: Arquivo {self.config_file} não encontrado. Usando defaults.")

        # Atributos de Coleta
        collection = self.config_data.get("collection", {})
        self.target_total_repos = collection.get("target_total_repos", 500)
        self.target_languages = collection.get("target_languages", ["Python", "Java", "JavaScript"])
        self.base_criteria = collection.get("base_criteria", "stars:>=1000 sort:stars-desc")
        
        # Atributos de Filtro
        filters = self.config_data.get("filters", {})
        self.min_prs = filters.get("min_prs_per_repo", 10)
        self.min_stars = filters.get("min_stars", 1000)
        self.min_contributors = filters.get("min_contributors", 50)

    def set_total_repos_override(self, total: int):
        """Permite que o argumento da CLI sobrescreva o valor do YAML."""
        if total and total > 0:
            self.target_total_repos = total

    @property
    def repos_per_language(self) -> int:
        """Calcula a distribuição equitativa entre as linguagens."""
        if not self.target_languages:
            return self.target_total_repos
        return max(1, self.target_total_repos // len(self.target_languages))