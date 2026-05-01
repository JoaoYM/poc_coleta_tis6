from src.models.experience_profile import ExperienceProfile

class ExperienceClassifier:
    """
    Especialista na regra de negócio de classificação de desenvolvedores.
    Isola a lógica de categorias da extração de dados brutos.
    """
    @staticmethod
    def classify(prior_prs: int, prior_merged: int, approved_reviews: int, changes_reviews: int) -> ExperienceProfile:
        formal_reviews = approved_reviews + changes_reviews
        acceptance_rate = (prior_merged / prior_prs) if prior_prs > 0 else 0.0

        # Lógica de Classificação Híbrida
        if formal_reviews >= 5:
            category = "Core Reviewer"
        elif prior_prs >= 2 and acceptance_rate >= 0.75:
            category = "Reliable Author"
        elif prior_prs >= 2 and acceptance_rate < 0.75:
            category = "Noisy Author"
        else:
            category = "Novice"

        return ExperienceProfile(prior_prs, round(acceptance_rate, 2), formal_reviews, category)

    @staticmethod
    def get_fallback() -> ExperienceProfile:
        """Retorna o perfil padrão em caso de falha da API."""
        return ExperienceProfile(0, 0.0, 0, "Novice")