import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

class DataVisualizer:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.figures_dir = self.base_path / "reports" / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuração estética para publicações científicas
        sns.set_theme(style="whitegrid", context="paper")

    def generate_analytical_plots(self, input_csv: str = "poc_analytical_dataset.csv"):
        input_path = self.data_dir / input_csv
        if not input_path.exists():
            print(f"❌ Erro: Dataset {input_csv} não encontrado.")
            return

        df = pd.read_csv(input_path)
        # Filtro de sanidade: remove latências irreais e foca no grosso dos dados (P95)
        # Isso evita que outliers extremos esmaguem visualmente o gráfico
        limit = df['first_review_latency_hours'].quantile(0.95)
        df_filtered = df[df['first_review_latency_hours'] <= limit].copy()

        # Categorização para o gráfico (Alta vs Baixa Centralidade)
        median_cent = df_filtered['author_degree_cent'].median()
        df_filtered['centrality_group'] = df_filtered['author_degree_cent'].apply(
            lambda x: 'Alta Centralidade' if x > median_cent else 'Baixa Centralidade'
        )

        print(f"\n🎨 Gerando gráficos de distribuição (limite visual: {limit:.1f}h)...")

        # Gráfico 1: Boxplot de Centralidade vs Latência (RQ1)
        plt.figure(figsize=(10, 6))
        ax = sns.boxplot(
            data=df_filtered, 
            x='centrality_group', 
            y='first_review_latency_hours',
            palette="Set2",
            showfliers=False # Outliers já controlados pelo filtro P95
        )
        plt.title("RQ1: Distribuição do Tempo de Revisão por Nível de Centralidade", fontsize=14)
        plt.xlabel("Grupo de Centralidade do Autor", fontsize=12)
        plt.ylabel("Tempo até o Primeiro Review (Horas)", fontsize=12)
        
        output_rq1 = self.figures_dir / "rq1_latency_distribution.png"
        plt.savefig(output_rq1, dpi=300, bbox_inches='tight')
        plt.close()

        # Gráfico 2: Violin Plot facetado por Experiência (RQ2)
        # Ajuda a ver a "massa" de dados onde os novatos sofrem mais
        plt.figure(figsize=(12, 7))
        # Criando a coluna de experiência baseada na lógica da Fase 4
        pr_counts = df_filtered['author'].value_counts()
        experientes_list = pr_counts[pr_counts > 1].index
        df_filtered['experience_level'] = df_filtered['author'].apply(
            lambda x: 'Experiente' if x in experientes_list else 'Novato'
        )

        sns.violinplot(
            data=df_filtered, 
            x='experience_level', 
            y='first_review_latency_hours', 
            hue='centrality_group',
            split=True,
            inner="quart",
            palette="muted",
            cut=0
        )
        plt.title("RQ2: Impacto da Centralidade Moderado pela Experiência", fontsize=14)
        plt.xlabel("Nível de Experiência do Autor", fontsize=12)
        plt.ylabel("Tempo até o Primeiro Review (Horas)", fontsize=12)
        
        output_rq2 = self.figures_dir / "rq2_experience_moderation.png"
        plt.savefig(output_rq2, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Gráficos salvos em: {self.figures_dir}")