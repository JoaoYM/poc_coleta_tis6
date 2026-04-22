import pandas as pd
import numpy as np
from scipy.stats import spearmanr, mannwhitneyu
from pathlib import Path
from src.utils.output_formatter import RepositoryOutputFormatter

class StatisticalAnalyzer:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.output = RepositoryOutputFormatter()

    def _cohens_d(self, group1: pd.Series, group2: pd.Series) -> float:
        """Calcula o tamanho do efeito (Cohen's d) entre dois grupos."""
        n1, n2 = len(group1), len(group2)
        if n1 == 0 or n2 == 0: return 0.0
        
        var1, var2 = group1.var(), group2.var()
        # Desvio padrão agrupado (pooled standard deviation)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        if pooled_std == 0: return 0.0
        return (group1.mean() - group2.mean()) / pooled_std

    def run_analysis(self, input_csv: str = "poc_analytical_dataset.csv"):
        input_path = self.data_dir / input_csv
        if not input_path.exists():
            print(f"❌ Erro: Dataset analítico {input_csv} não encontrado.")
            return

        df = pd.read_csv(input_path)
        print(f"\n📊 Iniciando Análise Estatística MSR ({len(df)} PRs válidos)")

        # Limpeza básica: Remove PRs com latência zerada ou negativa (ruídos de API)
        df = df[df['first_review_latency_hours'] > 0]

        print("\n" + "="*50)
        print(" RQ1: Centralidade vs Tempo de Revisão")
        print("="*50)
        
        # Correlação de Spearman (Não-paramétrica)
        r_deg, p_deg = spearmanr(df['author_degree_cent'], df['first_review_latency_hours'])
        print(f"🔹 Correlação (Degree Centrality x Latency):")
        print(f"   Spearman ρ: {r_deg:.3f} | p-value: {p_deg:.4e}")
        
        # Mann-Whitney U: Alta vs Baixa Centralidade
        # Usando a mediana para dividir os grupos de forma robusta
        median_cent = df['author_degree_cent'].median()
        high_cent = df[df['author_degree_cent'] > median_cent]['first_review_latency_hours']
        low_cent = df[df['author_degree_cent'] <= median_cent]['first_review_latency_hours']
        
        stat, p_mw = mannwhitneyu(high_cent, low_cent, alternative='two-sided')
        d = self._cohens_d(high_cent, low_cent)
        
        print(f"\n🔹 Comparação de Grupos (Alta vs Baixa Centralidade):")
        print(f"   Média Alta Cent: {high_cent.mean():.1f}h | Média Baixa Cent: {low_cent.mean():.1f}h")
        print(f"   Mann-Whitney U: {stat} | p-value: {p_mw:.4e}")
        print(f"   Effect Size (Cohen's d): {d:.3f}")


        print("\n" + "="*50)
        print(" RQ2: Moderação por Experiência (Novatos vs Experientes)")
        print("="*50)
        
        # Proxy de experiência para a POC: Quantidade de PRs submetidos pelo autor no dataset
        pr_counts = df['author'].value_counts()
        # Consideramos "Experiente" quem tem mais de 1 PR nesta janela temporal curta da POC
        experientes_list = pr_counts[pr_counts > 1].index
        
        df['is_experienced'] = df['author'].isin(experientes_list)
        novatos = df[~df['is_experienced']]
        experientes = df[df['is_experienced']]
        
        r_nov, p_nov = spearmanr(novatos['author_degree_cent'], novatos['first_review_latency_hours'])
        r_exp, p_exp = spearmanr(experientes['author_degree_cent'], experientes['first_review_latency_hours'])
        
        print(f"🔹 Novatos ({len(novatos)} PRs): Spearman ρ = {r_nov:.3f} (p={p_nov:.4f})")
        print(f"🔹 Experientes ({len(experientes)} PRs): Spearman ρ = {r_exp:.3f} (p={p_exp:.4f})")


        print("\n" + "="*50)
        print(" RQ3: Assimetria de Centralidade (Distância Estrutural)")
        print("="*50)
        
        # Correlação entre o Delta de Centralidade e a Latência
        r_asym, p_asym = spearmanr(df['centrality_asymmetry'], df['first_review_latency_hours'])
        print(f"🔹 Correlação (Assimetria x Latency):")
        print(f"   Spearman ρ: {r_asym:.3f} | p-value: {p_asym:.4e}")
        
        print("\n✅ Testes estatísticos da POC concluídos com sucesso!")