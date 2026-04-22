import pandas as pd
import networkx as nx
from pathlib import Path

class GraphModeler:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"

    def build_and_calculate(self, input_csv: str = "poc_prs_extracted.csv", output_csv: str = "poc_analytical_dataset.csv"):
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
        
        for repo_name, df_repo in grouped_repos:
            print(f"🕸️  Montando rede para: {repo_name}...")
            
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
            # Como a rede pode ser grande, networkx lida bem com isso na RAM
            betweenness_cent = nx.betweenness_centrality(G, weight='weight')
            
            # 3. Mapeamento das métricas de volta para o DataFrame do repositório
            # Mapeia a centralidade do Autor do PR
            df_repo['author_degree_cent'] = df_repo['author'].map(degree_cent).fillna(0)
            df_repo['author_betweenness_cent'] = df_repo['author'].map(betweenness_cent).fillna(0)
            
            # Mapeia a centralidade do Revisor do PR
            df_repo['reviewer_degree_cent'] = df_repo['primary_reviewer'].map(degree_cent).fillna(0)
            df_repo['reviewer_betweenness_cent'] = df_repo['primary_reviewer'].map(betweenness_cent).fillna(0)
            
            # 4. Operacionalização da Variável Independente da RQ3 (Assimetria)
            # Delta absoluto entre a centralidade do autor e do revisor
            df_repo['centrality_asymmetry'] = abs(df_repo['author_degree_cent'] - df_repo['reviewer_degree_cent'])
            
            enriched_dfs.append(df_repo)

        # 5. Consolidação Final
        df_final = pd.concat(enriched_dfs, ignore_index=True)
        
        output_path = self.data_dir / output_csv
        df_final.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ Dataset analítico gerado com sucesso!")
        print(f"💾 Salvo em: {output_path}")
        print(f"📊 Total de PRs processados: {len(df_final)}")