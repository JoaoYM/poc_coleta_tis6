from dataclasses import dataclass

@dataclass
class ExperienceProfile:
    """Estrutura de dados Limpa (Clean Code) para o perfil de experiência"""
    prior_prs: int
    acceptance_rate: float
    formal_reviews: int
    category: str