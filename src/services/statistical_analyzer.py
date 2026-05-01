import pandas as pd
from pathlib import Path
from typing import List
from src.utils.output.output_formatter import RepositoryOutputFormatter
from src.services.strategies.rqs import AbstractAnalysisStrategy

class StatisticalAnalyzer:
    """
    Orquestrador de Análises Estatísticas (Padrão Strategy).
    Garante o filtro global de validade e delega a execução das RQs.
    """
    def __init__(self, strategies: List[AbstractAnalysisStrategy] = None):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.output = RepositoryOutputFormatter()
        
        # Injeção das estratégias (RQs)
        self.strategies = strategies or []

    def run_analysis(self, input_csv: str = "poc_analytical_dataset.csv"):
        input_path = self.data_dir / input_csv
        if not input_path.exists():
            print(f"❌ Erro: Dataset analítico {input_csv} não encontrado.")
            return

        df = pd.read_csv(input_path)
        print(f"\n📊 Carregando Dataset MSR ({len(df)} PRs brutos)...")

        # Filtro Global de Ameaça à Validade (Apenas latências reais)
        df_clean = df[df['first_review_latency_hours'] > 0].copy()
        print(f"🧹 Filtro de Latência > 0 aplicado: {len(df_clean)} PRs retidos para análise.")

        if not self.strategies:
            print("⚠️ Nenhuma estratégia (RQ) fornecida para execução.")
            return

        # Executa dinamicamente todas as RQs plugadas
        for strategy in self.strategies:
            strategy.execute(df_clean)

        print("\n✅ Testes estatísticos da POC concluídos com sucesso!")