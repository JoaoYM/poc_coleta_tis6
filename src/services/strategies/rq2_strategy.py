import pandas as pd
from scipy.stats import spearmanr
from src.services.strategies.rqs import AbstractAnalysisStrategy

class RQ2ExperienceStrategy(AbstractAnalysisStrategy):
    @property
    def name(self) -> str:
        return "RQ2: Moderação por Experiência (Novatos vs Experientes)"

    def execute(self, df: pd.DataFrame) -> None:
        print("\n" + "="*50)
        print(f" {self.name}")
        print("="*50)
        
        pr_counts = df['author'].value_counts()
        experientes_list = pr_counts[pr_counts > 1].index
        
        # Usa .copy() no slice para evitar o warning "SettingWithCopyWarning" do Pandas
        df_analysis = df.copy()
        df_analysis['is_experienced'] = df_analysis['author'].isin(experientes_list)
        
        novatos = df_analysis[~df_analysis['is_experienced']]
        experientes = df_analysis[df_analysis['is_experienced']]
        
        r_nov, p_nov = spearmanr(novatos['author_degree_cent'], novatos['first_review_latency_hours'])
        r_exp, p_exp = spearmanr(experientes['author_degree_cent'], experientes['first_review_latency_hours'])
        
        print(f"🔹 Novatos ({len(novatos)} PRs): Spearman ρ = {r_nov:.3f} (p={p_nov:.4f})")
        print(f"🔹 Experientes ({len(experientes)} PRs): Spearman ρ = {r_exp:.3f} (p={p_exp:.4f})")