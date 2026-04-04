"""
Geração de gráficos complementares avançados baseados nas referências
Piktochart e Opus Pesquisa (Heatmaps, Boxplots e Histogramas).
"""

from pathlib import Path
import matplotlib
import pandas as pd
import seaborn as sns
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Configuração de diretórios
ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "data" / "ck_metrics_consolidated.csv"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"


def configure_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update({
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "figure.titlesize": 16,
    })


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH)
    df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True, errors="coerce")
    reference_date = pd.to_datetime("now", utc=True)
    df["maturity_years"] = (reference_date - df["createdAt"]).dt.days / 365.25
    
    cols = ["stargazerCount", "releases_count", "maturity_years", "loc_total", "cbo_median", "dit_median", "lcom_median"]
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    return df.dropna(subset=cols)


def plot_correlation_heatmap(df: pd.DataFrame) -> None:
    """Gera um Mapa de Calor (Heatmap) com todas as variáveis juntas."""
    cols_map = {
        "stargazerCount": "Estrelas",
        "maturity_years": "Idade (Anos)",
        "releases_count": "Releases",
        "loc_total": "Tamanho (LOC)",
        "cbo_median": "Acoplamento (CBO)",
        "dit_median": "Herança (DIT)",
        "lcom_median": "Falta de Coesão (LCOM)"
    }
    
    corr_df = df[list(cols_map.keys())].rename(columns=cols_map)
    # Correlação de Spearman pois os dados não têm distribuição normal
    corr_matrix = corr_df.corr(method="spearman")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Paleta divergente (Azul para positivo, Vermelho para negativo)
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="vlag", 
                center=0, square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax)
    
    plt.title("Mapa de Calor: Correlação de Spearman entre Todas as Variáveis", pad=20)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "extra_01_correlation_heatmap.png", dpi=300)
    plt.close()
    print("✅ Mapa de Calor gerado!")


def plot_cbo_boxplot_by_size(df: pd.DataFrame) -> None:
    """Gera Gráficos de Caixa (Boxplot) categorizando os repositórios por tamanho."""
    # Divide os repositórios em 3 categorias baseadas nos percentis de LOC
    df["Tamanho"] = pd.qcut(df["loc_total"], q=3, labels=["Pequeno", "Médio", "Grande"])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Boxplot focado no CBO (Acoplamento)
    sns.boxplot(data=df, x="Tamanho", y="cbo_median", palette="Set2", ax=ax, showfliers=False)
    # Adiciona os pontos por cima para mostrar a densidade (Swarmplot / Dispersão)
    sns.stripplot(data=df, x="Tamanho", y="cbo_median", color="black", alpha=0.4, jitter=True, ax=ax)
    
    plt.title("Distribuição do Acoplamento (CBO) por Categoria de Tamanho", pad=15)
    plt.xlabel("Categoria de Tamanho (Baseado no LOC)")
    plt.ylabel("Mediana do CBO (Acoplamento)")
    
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "extra_02_boxplot_cbo_size.png", dpi=300)
    plt.close()
    print("✅ Gráfico de Caixa (Boxplot) gerado!")


def plot_metrics_distributions(df: pd.DataFrame) -> None:
    """Gera Histogramas de densidade (KDE) para as métricas de qualidade."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = [
        ("cbo_median", "Distribuição do CBO", "#3b82f6"),
        ("dit_median", "Distribuição do DIT", "#10b981"),
        ("lcom_median", "Distribuição do LCOM", "#ef4444")
    ]
    
    for ax, (col, title, color) in zip(axes, metrics):
        # Limita visualmente até o percentil 95 para ignorar outliers extremos
        p95 = df[col].quantile(0.95)
        filtered_data = df[df[col] <= p95]
        
        sns.histplot(data=filtered_data, x=col, kde=True, color=color, ax=ax, bins=15)
        ax.set_title(title)
        ax.set_xlabel("Valor da Mediana no Repositório")
        ax.set_ylabel("Frequência (Qtd de Repositórios)")

    fig.suptitle("Histogramas de Distribuição das Métricas de Qualidade Interna", fontsize=16, y=1.05)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "extra_03_quality_distributions.png", dpi=300)
    plt.close()
    print("✅ Histogramas de Distribuição gerados!")


def main() -> None:
    configure_plot_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_data()
    print(f"📊 Processando {len(df)} repositórios para gráficos avançados...")
    
    plot_correlation_heatmap(df)
    plot_cbo_boxplot_by_size(df)
    plot_metrics_distributions(df)
    
    print(f"\n🚀 Tudo pronto! Verifique a pasta {FIGURES_DIR}")


if __name__ == "__main__":
    main()