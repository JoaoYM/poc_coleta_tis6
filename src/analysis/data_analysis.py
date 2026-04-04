import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from pathlib import Path
from datetime import datetime, timezone

class Lab02DataAnalyzer:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_file = self.base_path / "data" / "ck_metrics_consolidated.csv"
        self.figures_dir = self.base_path / "reports" / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuração visual dos gráficos
        sns.set_theme(style="whitegrid")
        
    def load_and_prepare_data(self):
        """Lê o CSV e calcula campos derivados como a Maturidade (Idade em anos)"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.data_file}. Rode a extração primeiro.")
            
        df = pd.read_csv(self.data_file)
        
        # Remove repositórios que por ventura falharam e não têm métricas
        df = df.dropna(subset=['cbo_median', 'dit_median', 'lcom_median'])
        
        # Calcula Maturidade (Idade em anos) com base no createdAt
        current_date = pd.to_datetime(datetime.now(timezone.utc))
        df['createdAt'] = pd.to_datetime(df['createdAt'])
        df['maturity_years'] = (current_date - df['createdAt']).dt.days / 365.25
        
        return df

    def analyze_and_plot(self, df: pd.DataFrame, independent_var: str, independent_label: str, rq_name: str):
        """
        Calcula a correlação de Spearman e gera gráficos de dispersão (Scatter) 
        para CBO, DIT e LCOM usando a mediana (conforme solicitado no roteiro).
        """
        dependent_vars = {
            'cbo_median': 'CBO (Acoplamento)',
            'dit_median': 'DIT (Herança)',
            'lcom_median': 'LCOM (Coesão)'
        }
        
        print(f"\n{'='*50}\n📊 Resultados para {rq_name}: {independent_label} vs Qualidade\n{'='*50}")
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(f'{rq_name}: Impacto de {independent_label} na Qualidade do Código', fontsize=16)
        
        for i, (dep_var, dep_label) in enumerate(dependent_vars.items()):
            # Corrige possíveis NaNs nas colunas
            clean_df = df[[independent_var, dep_var]].dropna()
            
            # Cálculo de Correlação de Spearman
            corr, p_value = spearmanr(clean_df[independent_var], clean_df[dep_var])
            
            # Log no terminal
            print(f"-> {dep_label}:")
            print(f"   Correlação (Spearman): {corr:.4f}")
            print(f"   P-Value: {p_value:.4e} {'(Significativo)' if p_value < 0.05 else '(Não Significativo)'}")
            
            # Plotagem do Gráfico de Dispersão com Linha de Tendência
            sns.regplot(
                data=clean_df, 
                x=independent_var, 
                y=dep_var, 
                ax=axes[i],
                scatter_kws={'alpha': 0.5},
                line_kws={'color': 'red'}
            )
            axes[i].set_title(f'{independent_label} vs {dep_label}\nCorr: {corr:.2f}')
            axes[i].set_xlabel(independent_label)
            axes[i].set_ylabel(dep_label)

        plt.tight_layout()
        output_file = self.figures_dir / f"{rq_name.replace(' ', '_').lower()}.png"
        plt.savefig(output_file, dpi=300)
        plt.close()
        print(f"💾 Gráfico salvo em: {output_file}")

    def run_all_analyses(self):
        df = self.load_and_prepare_data()
        print(f"✅ Dados carregados com sucesso! Total de repositórios válidos: {len(df)}")
        
        # RQ 01: Popularidade (Estrelas)
        self.analyze_and_plot(df, 'stargazerCount', 'Estrelas (Popularidade)', 'RQ 01')
        
        # RQ 02: Maturidade (Anos)
        self.analyze_and_plot(df, 'maturity_years', 'Idade em Anos (Maturidade)', 'RQ 02')
        
        # RQ 03: Atividade (Releases)
        self.analyze_and_plot(df, 'releases_count', 'Total de Releases (Atividade)', 'RQ 03')
        
        # RQ 04: Tamanho (LOC Total do Repo ou LOC Mediano da classe, usando LOC Total como métrica de tamanho do software)
        self.analyze_and_plot(df, 'loc_total', 'Tamanho Total (LOC)', 'RQ 04')
        
        print("\n🎉 Todas as análises concluídas! Verifique a pasta reports/figures/")

if __name__ == "__main__":
    analyzer = Lab02DataAnalyzer()
    analyzer.run_all_analyses()