import pandas as pd
from scipy.stats import spearmanr, mannwhitneyu
from src.services.strategies.rqs import AbstractAnalysisStrategy
from src.utils.data.stats_utils import cohens_d

class RQ1CentralityStrategy(AbstractAnalysisStrategy):
    @property
    def name(self) -> str:
        return "RQ1: Centralidade vs Tempo de Revisão"

    def execute(self, df: pd.DataFrame) -> None:
        print("\n" + "="*50)
        print(f" {self.name}")
        print("="*50)
        
        # Correlação de Spearman
        r_deg, p_deg = spearmanr(df['author_degree_cent'], df['first_review_latency_hours'])
        print(f"🔹 Correlação (Degree Centrality x Latency):")
        print(f"   Spearman ρ: {r_deg:.3f} | p-value: {p_deg:.4e}")
        
        # Mann-Whitney U: Alta vs Baixa Centralidade
        median_cent = df['author_degree_cent'].median()
        high_cent = df[df['author_degree_cent'] > median_cent]['first_review_latency_hours']
        low_cent = df[df['author_degree_cent'] <= median_cent]['first_review_latency_hours']
        
        stat, p_mw = mannwhitneyu(high_cent, low_cent, alternative='two-sided')
        d = cohens_d(high_cent, low_cent)
        
        print(f"\n🔹 Comparação de Grupos (Alta vs Baixa Centralidade):")
        print(f"   Média Alta Cent: {high_cent.mean():.1f}h | Média Baixa Cent: {low_cent.mean():.1f}h")
        print(f"   Mann-Whitney U: {stat} | p-value: {p_mw:.4e}")
        print(f"   Effect Size (Cohen's d): {d:.3f}")