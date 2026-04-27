import pandas as pd
import networkx as nx
from pathlib import Path

class GraphModeler:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"

    def build_and_calculate(self, input_csv: str = "poc_prs_sanitized.csv", output_csv: str = "poc_analytical_dataset.csv"):
        """
        Lê os PRs, constrói os grafos por repositório, calcula as centralidades 
        e gera o dataset pronto para a estatística.
        """
        input_path = self.data_dir / input_csv
        if not input_path.exists():
            print(f"❌ Erro: Arquivo {input_csv} não encontrado!")
            return

        print(f"\n🧠 Iniciando Modelagem de Grafos (Lendo {len(pd.read_csv(input_path))} PRs)...")
        df_prs = pd.read_csv(input_path)
        
        # Lista para armazenar os dataframes enriquecidos de cada repositório
        enriched_dfs = []
        
        # Precisamos agrupar por repositório, pois a centralidade 
        # só faz sentido dentro da comunidade do próprio projeto.
        grouped_repos = df_prs.groupby('repository')
        
        for repo_name, df_repo_orig in grouped_repos:
            print(f"🕸️  Montando rede para: {repo_name}...")
            
            # .copy() protege contra o SettingWithCopyWarning do Pandas
            df_repo = df_repo_orig.copy()
            
            # 1. Construção do Grafo Direcionado (Revisor -> Autor)
            # Usamos MultiDiGraph caso haja múltiplas revisões entre a mesma dupla
            G = nx.DiGraph() 
            
            # Adiciona as arestas (edges) baseadas nas interações do PR
            for _, row in df_repo.iterrows():
                reviewer = row['primary_reviewer']
                author = row['author']
                
                if G.has_edge(reviewer, author):
                    G[reviewer][author]['weight'] += 1
                else:
                    G.add_edge(reviewer, author, weight=1)
            
            # 2. Cálculo das Métricas de Centralidade
            # Degree Centrality: Volume total de conexões
            degree_cent = nx.degree_centrality(G)
            
            # Betweenness Centrality: Influência/Ponte na rede (RQ1)
            betweenness_cent = nx.betweenness_centrality(G, weight='weight')
            
            # 3. Mapeamento das métricas de volta para o DataFrame do repositório
            df_repo['author_degree_cent'] = df_repo['author'].map(degree_cent).fillna(0)
            df_repo['author_betweenness_cent'] = df_repo['author'].map(betweenness_cent).fillna(0)
            
            df_repo['reviewer_degree_cent'] = df_repo['primary_reviewer'].map(degree_cent).fillna(0)
            df_repo['reviewer_betweenness_cent'] = df_repo['primary_reviewer'].map(betweenness_cent).fillna(0)
            
            # 4. Operacionalização da Variável Independente da RQ3 (Assimetria)
            df_repo['centrality_asymmetry'] = abs(df_repo['author_degree_cent'] - df_repo['reviewer_degree_cent'])
            
            # 5. Estrutura Core-Periphery (Ranqueamento Relativo do Repositório)
            if len(df_repo) > 0:
                p50 = df_repo['author_degree_cent'].quantile(0.50)
                p85 = df_repo['author_degree_cent'].quantile(0.85)
            else:
                p50, p85 = 0, 0

            def categorize_centrality(c_value):
                # A trava c_value > 0 impede que autores zerados caiam como Regular/Core
                # caso a distribuição seja muito enviesada para baixo (muitos zeros).
                if c_value >= p85 and c_value > 0:
                    return 'Core (Top 15%)'
                elif c_value >= p50 and c_value > 0:
                    return 'Regular (Classe Média)'
                else:
                    return 'Periférico (Bottom 50%)'

            df_repo['centrality_group'] = df_repo['author_degree_cent'].apply(categorize_centrality)
            
            enriched_dfs.append(df_repo)

        # 6. Consolidação Final
        if enriched_dfs:
            df_final = pd.concat(enriched_dfs, ignore_index=True)
            output_path = self.data_dir / output_csv
            df_final.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"\n✅ Dataset analítico gerado com sucesso!")
            print(f"💾 Salvo em: {output_path}")
            print(f"📊 Total de PRs processados: {len(df_final)}")
        else:
            print("❌ Erro: Nenhum dado válido encontrado para modelar.")