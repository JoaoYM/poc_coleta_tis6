"""
Geração de gráficos e estatísticas para o Laboratório 02.
Analisa a correlação entre métricas de processo/tamanho e qualidade (CBO, DIT, LCOM).
"""

from pathlib import Path
import matplotlib
import pandas as pd
import seaborn as sns
from scipy import stats
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Configuração de diretórios
ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "data" / "ck_metrics_consolidated.csv"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"


def configure_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.titlesize": 14,
        }
    )


def load_and_prepare_data(dataset_path: Path) -> pd.DataFrame:
    df = pd.read_csv(dataset_path)
    
    # Converte datas e calcula a Maturidade (Idade em Anos)
    df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True, errors="coerce")
    reference_date = pd.to_datetime("now", utc=True)
    df["maturity_years"] = (reference_date - df["createdAt"]).dt.days / 365.25
    
    # Garante que as colunas numéricas estão corretas e remove NaNs
    numeric_cols = [
        "stargazerCount", "releases_count", "maturity_years", "loc_total",
        "cbo_median", "dit_median", "lcom_median"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df = df.dropna(subset=numeric_cols)
    return df


def print_summary_statistics(df: pd.DataFrame) -> None:
    """Imprime as estatísticas descritivas solicitadas no roteiro."""
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DESCRITIVAS (MÉDIA, MEDIANA, DESVIO PADRÃO)")
    print("="*60)
    
    metrics = {
        "CBO (Acoplamento)": "cbo_median",
        "DIT (Herança)": "dit_median",
        "LCOM (Coesão)": "lcom_median",
        "LOC (Tamanho)": "loc_total",
        "Estrelas (Popularidade)": "stargazerCount",
        "Idade em Anos (Maturidade)": "maturity_years",
        "Releases (Atividade)": "releases_count"
    }
    
    for label, col in metrics.items():
        if col in df.columns:
            mean = df[col].mean()
            median = df[col].median()
            std = df[col].std()
            print(f"🔹 {label}:")
            print(f"   Média: {mean:.2f} | Mediana: {median:.2f} | Desvio Padrão: {std:.2f}")


def plot_correlation(df: pd.DataFrame, independent_var: str, x_label: str, rq_title: str, output_filename: str) -> None:
    """Gera o gráfico de dispersão com linha de tendência e anotação de Spearman."""
    
    dependent_vars = [
        ("cbo_median", "CBO (Acoplamento)"),
        ("dit_median", "DIT (Árvore de Herança)"),
        ("lcom_median", "LCOM (Falta de Coesão)")
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(rq_title, fontweight='bold', y=1.05)
    
    print(f"\n🚀 Resultados {rq_title.split('—')[0].strip()}:")
    
    for i, (dep_var, y_label) in enumerate(dependent_vars):
        ax = axes[i]
        
        # Filtra outliers extremos visualmente para não achatar o gráfico (opcional, ajuda na visualização)
        # Calculando o percentil 95 para limitar o eixo X visualmente (os dados do teste estatístico não são alterados)
        x_p95 = df[independent_var].quantile(0.95)
        y_p95 = df[dep_var].quantile(0.95)
        
        # Plot do scatter com regressão
        sns.regplot(
            data=df, 
            x=independent_var, 
            y=dep_var, 
            ax=ax,
            scatter_kws={'alpha': 0.4, 'color': '#2563EB', 's': 20},
            line_kws={'color': '#DC2626', 'linewidth': 2}
        )
        
        # Ajuste de limites para visualização mais limpa (foca onde 95% dos dados estão)
        ax.set_xlim(left=-0.5, right=x_p95 * 1.1)
        ax.set_ylim(bottom=-0.5, top=y_p95 * 1.5)
        
        # Teste de Spearman
        rho, p_value = stats.spearmanr(df[independent_var], df[dep_var])
        
        # Log no terminal
        print(f"  -> {y_label}: ρ (Spearman) = {rho:+.4f} | p-value = {p_value:.2e}")
        
        # Anotação no gráfico
        significancia = "Significativo" if p_value < 0.05 else "Não Significativo"
        bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9)
        ax.text(
            0.05, 0.95, 
            f"Spearman (ρ): {rho:.3f}\nValor-p: {p_value:.1e}\n({significancia})", 
            transform=ax.transAxes, 
            fontsize=10, 
            verticalalignment='top', 
            bbox=bbox_props
        )
        
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

    fig.tight_layout()
    output_path = FIGURES_DIR / output_filename
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_plot_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        df = load_and_prepare_data(DATASET_PATH)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {DATASET_PATH}")
        print("Aguarde a extração finalizar ou verifique o caminho.")
        return

    print(f"✅ Dataset carregado! Repositórios analisados: {len(df)}")
    
    # 1. Imprime Estatísticas (Exigência do roteiro)
    print_summary_statistics(df)
    
    # 2. Gera os gráficos de correlação (Exigência bônus)
    plot_correlation(
        df, "stargazerCount", "Total de Estrelas", 
        "RQ01 — Correlação entre Popularidade e Qualidade", "rq01_popularity_vs_quality.png"
    )
    
    plot_correlation(
        df, "maturity_years", "Idade do Repositório (Anos)", 
        "RQ02 — Correlação entre Maturidade e Qualidade", "rq02_maturity_vs_quality.png"
    )
    
    plot_correlation(
        df, "releases_count", "Total de Releases", 
        "RQ03 — Correlação entre Atividade (Releases) e Qualidade", "rq03_activity_vs_quality.png"
    )
    
    plot_correlation(
        df, "loc_total", "Linhas de Código Totais (LOC)", 
        "RQ04 — Correlação entre Tamanho (LOC) e Qualidade", "rq04_size_vs_quality.png"
    )
    
    print(f"\n🎉 Gráficos salvos com sucesso na pasta: {FIGURES_DIR}")


if __name__ == "__main__":
    main()