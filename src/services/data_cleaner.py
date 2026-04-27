import pandas as pd
from pathlib import Path

class DataCleaner:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"

    def sanitize_extracted_data(self, input_csv: str = "poc_prs_extracted.csv", output_csv: str = "poc_prs_sanitized.csv"):
        input_path = self.data_dir / input_csv
        if not input_path.exists():
            print(f"❌ Erro: {input_csv} não encontrado.")
            return

        print("\n🧹 Iniciando Sanitização de Dados MSR...")
        df = pd.read_csv(input_path)
        original_count = len(df)
        original_repos = df['repository'].nunique()

        # ---------------------------------------------------------
        # REGRA 1: Filtro de Micro-Repositórios (Densidade Mínima)
        # ---------------------------------------------------------
        MIN_PRS = 10
        # Conta quantos PRs cada repositório tem
        repo_counts = df['repository'].value_counts()
        
        # Filtra os repositórios que atingiram o limiar
        valid_repos = repo_counts[repo_counts >= MIN_PRS].index
        
        # Mantém no DataFrame apenas os PRs que pertencem a repositórios válidos
        df_clean = df[df['repository'].isin(valid_repos)].copy()
        
        repos_dropped = original_repos - len(valid_repos)
        prs_dropped_by_size = original_count - len(df_clean)

        # ---------------------------------------------------------
        # REGRA 2: Remoção de Fallbacks Críticos da API (Opcional, mas recomendado)
        # ---------------------------------------------------------
        # Se a API falhou, ela devolveu experience_category == "Novice" E prior_prs == 0
        # O problema é que isso se confunde com novatos reais. 
        # Uma heurística de segurança: Se o autor é o revisor principal de muitos PRs na nossa
        # amostra, mas consta como Novato (0 PRs anteriores), a API falhou para ele.
        
        # Encontra quem são os top revisores na amostra atual
        top_reviewers_in_sample = df_clean['primary_reviewer'].value_counts()
        active_reviewers = top_reviewers_in_sample[top_reviewers_in_sample > 2].index
        
        # Marca como anomalia: Autores que são revisores frequentes, mas o histórico diz que são Novatos Absolutos
        anomaly_mask = (df_clean['author'].isin(active_reviewers)) & (df_clean['prior_prs'] == 0)
        prs_dropped_by_anomaly = anomaly_mask.sum()
        
        # Remove as anomalias
        df_final = df_clean[~anomaly_mask]

        # ---------------------------------------------------------
        # SALVAMENTO
        # ---------------------------------------------------------
        output_path = self.data_dir / output_csv
        df_final.to_csv(output_path, index=False)

        print("="*50)
        print("📊 Relatório de Sanitização:")
        print(f"🔸 Total Inicial: {original_count} PRs | {original_repos} Repositórios")
        print(f"✂️  Descartados (Micro-Repos < {MIN_PRS}): {prs_dropped_by_size} PRs (de {repos_dropped} repos perdidos)")
        print(f"✂️  Descartados (Anomalias de API): {prs_dropped_by_anomaly} PRs")
        print(f"✅ Total Final Limpo: {len(df_final)} PRs | {df_final['repository'].nunique()} Repositórios saudáveis")
        print("="*50)

# Para rodar:
cleaner = DataCleaner()
cleaner.sanitize_extracted_data()