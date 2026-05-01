import pandas as pd
from scipy.stats import spearmanr
from src.services.strategies.rqs import AbstractAnalysisStrategy

class RQ3AsymmetryStrategy(AbstractAnalysisStrategy):
    @property
    def name(self) -> str:
        return "RQ3: Assimetria de Centralidade (Distância Estrutural)"

    def execute(self, df: pd.DataFrame) -> None:
        print("\n" + "="*50)
        print(f" {self.name}")
        print("="*50)
        
        r_asym, p_asym = spearmanr(df['centrality_asymmetry'], df['first_review_latency_hours'])
        print(f"🔹 Correlação (Assimetria x Latency):")
        print(f"   Spearman ρ: {r_asym:.3f} | p-value: {p_asym:.4e}")