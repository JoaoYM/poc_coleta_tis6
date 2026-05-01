import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.utils.output.output_formatter import RepositoryOutputFormatter
from src.models.experience_profile import ExperienceProfile
from src.models.experience_classifier import ExperienceClassifier
from src.infrastructure.graphql.client import GraphQLClient
from src.utils.filters.github_filters import is_human
from src.utils.time.time_utils import calculate_business_hours_latency, calculate_time_to_merge_hours

class ReviewDataExtractor:
    """
    Orquestrador da Fase 2.
    Lê a base de repositórios, aciona o cliente GraphQL e delega a matemática
    e as regras de negócio para os utilitários e classificadores especializados.
    """
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.query_file = self.base_path / "src" / "infrastructure" / "graphql" / "pr_query.graphql"
        self.output = RepositoryOutputFormatter()
        
        self.client = GraphQLClient(self.fetcher)
        self.experience_cache = {}

    def _get_query_content(self) -> str:
        if not self.query_file.exists():
            raise FileNotFoundError(f"Arquivo de query não encontrado: {self.query_file}")
        return self.query_file.read_text(encoding="utf-8")

    def _fetch_author_experience(self, repo_name: str, author_login: str, reference_date: datetime) -> ExperienceProfile:
        cache_key = f"{repo_name}:{author_login}"
        if cache_key in self.experience_cache:
            return self.experience_cache[cache_key]

        decay_date = reference_date - timedelta(days=730)
        date_filter = f"created:{decay_date.strftime('%Y-%m-%d')}..{reference_date.strftime('%Y-%m-%d')}"

        query = """
        query($searchAuthored: String!, $searchMerged: String!, $searchApproved: String!, $searchChanges: String!) {
          authored: search(query: $searchAuthored, type: ISSUE, first: 0) { issueCount }
          merged: search(query: $searchMerged, type: ISSUE, first: 0) { issueCount }
          approved: search(query: $searchApproved, type: ISSUE, first: 0) { issueCount }
          changes: search(query: $searchChanges, type: ISSUE, first: 0) { issueCount }
        }
        """

        variables = {
            "searchAuthored": f"repo:{repo_name} author:{author_login} is:pr {date_filter}",
            "searchMerged": f"repo:{repo_name} author:{author_login} is:pr is:merged {date_filter}",
            "searchApproved": f"repo:{repo_name} reviewed-by:{author_login} -author:{author_login} review:approved {date_filter}",
            "searchChanges": f"repo:{repo_name} reviewed-by:{author_login} -author:{author_login} review:changes_requested {date_filter}"
        }

        # O try/except e requests gigante virou uma única linha
        data = self.client.execute(query, variables, max_attempts=5, base_wait=2)
        
        if data:
            search_data = data.get('data', {})
            prior_prs = search_data.get('authored', {}).get('issueCount', 0)
            prior_merged = search_data.get('merged', {}).get('issueCount', 0)
            approved_reviews = search_data.get('approved', {}).get('issueCount', 0)
            changes_reviews = search_data.get('changes', {}).get('issueCount', 0)
            
            # Delega a inteligência para o domínio
            profile = ExperienceClassifier.classify(prior_prs, prior_merged, approved_reviews, changes_reviews)
        else:
            print(f"❌ Abortando cálculo de {author_login}. Assumindo Fallback (Novice).")
            profile = ExperienceClassifier.get_fallback()

        self.experience_cache[cache_key] = profile
        return profile

    def extract_prs_from_csv(self, input_csv: str = "poc_repos_merged_filter.csv", start_date: str = "2026-01-01", end_date: str = "2026-02-28"):
        input_path = self.data_dir / input_csv
        output_path = self.data_dir / "poc_prs_extracted.csv"
        
        if output_path.exists():
            output_path.unlink()
            print(f"🧹 Arquivo anterior {output_path.name} limpo para nova extração.")

        if not input_path.exists():
            print(f"❌ Erro: Arquivo {input_csv} não encontrado.")
            return

        df_repos = pd.read_csv(input_path)
        query_content = self._get_query_content()
        total_repos = len(df_repos)

        self.output.print_fetch_start("GraphQL PR Extractor", total_repos)
        start_time = time.time()

        for index, row in df_repos.iterrows():
            repo_name = row['name']
            pr_query = f"repo:{repo_name} is:pr is:merged -is:draft merged:{start_date}..{end_date}"
            cursor = None
            has_next = True
            repo_prs_data = [] 
            
            current_time = time.time()
            elapsed_seconds = current_time - start_time
            elapsed_str = str(timedelta(seconds=int(elapsed_seconds)))
            
            if index > 0:
                avg_time_per_repo = elapsed_seconds / index
                eta_seconds = avg_time_per_repo * (total_repos - index)
                eta_str = str(timedelta(seconds=int(eta_seconds)))
            else:
                eta_str = "Calculando..."

            print(f"\n" + "="*60)
            print(f"📡 [{index+1}/{total_repos}] Extraindo PRs de: {repo_name}")
            print(f"⏱️ Decorrido: {elapsed_str} | ⏳ ETA: {eta_str}")
            print("="*60)
            
            while has_next:
                variables = {"prQuery": pr_query, "cursor": cursor}
                
                # A lógica maciça de paginação e retry reduziu a isso
                data = self.client.execute(query_content, variables, max_attempts=5, base_wait=3)
                
                if not data:
                    print(f"⏭️ Pulando o restante de {repo_name} após falhas consecutivas da API.")
                    break 
                    
                search_results = data.get('data', {}).get('search', {})
                
                for edge in search_results.get('edges', []):
                    pr_node = edge.get('node')
                    if not pr_node: continue
                    
                    author_data = pr_node.get('author')
                    author_login = author_data.get('login') if author_data else None
                    
                    # Usa o filtro extraído
                    if not is_human(author_login):
                        continue
                        
                    pr_info = self._process_pr_node(repo_name, pr_node, author_login)
                    if pr_info:
                        repo_prs_data.append(pr_info)

                page_info = search_results.get('pageInfo', {})
                has_next = page_info.get('hasNextPage', False)
                cursor = page_info.get('endCursor')
                time.sleep(0.5)

            if repo_prs_data:
                df_chunk = pd.DataFrame(repo_prs_data)
                write_mode = 'a' if output_path.exists() else 'w'
                write_header = not output_path.exists()
                df_chunk.to_csv(output_path, mode=write_mode, header=write_header, index=False, encoding='utf-8')
                print(f"💾 Checkpoint: {len(repo_prs_data)} PRs salvos no disco.")
            else:
                print(f"⚠️ Nenhum PR válido extraído para {repo_name}.")

        total_elapsed = str(timedelta(seconds=int(time.time() - start_time)))
        print(f"\n✅ Extração finalizada com sucesso! Tempo total: {total_elapsed}")
        self.output.print_save_success(str(output_path))

    def _process_pr_node(self, repo_name: str, pr_node: Dict[str, Any], author_login: str) -> Dict[str, Any]:
        pr_created_at = pd.to_datetime(pr_node.get('createdAt'))
        pr_merged_at = pd.to_datetime(pr_node.get('mergedAt')) if pr_node.get('mergedAt') else None
        
        human_reviews = []
        human_comments_count = 0
        
        for review in pr_node.get('reviews', {}).get('nodes', []):
            if not review or not review.get('author'): continue
            reviewer_login = review['author'].get('login')
            if is_human(reviewer_login) and reviewer_login != author_login:
                human_reviews.append({
                    "reviewer": reviewer_login,
                    "date": pd.to_datetime(review['createdAt']),
                    "state": review.get('state', 'UNKNOWN')
                })
                
        for comment in pr_node.get('comments', {}).get('nodes', []):
            if not comment or not comment.get('author'): continue
            commenter_login = comment['author'].get('login')
            if is_human(commenter_login):
                human_comments_count += 1
                
        if not human_reviews:
            return None
            
        human_reviews.sort(key=lambda x: x['date'])
        first_review = human_reviews[0]
        first_review_date = first_review['date']
        
        # Delega os cálculos matemáticos complexos
        latency_hours = calculate_business_hours_latency(pr_created_at, first_review_date)
        time_to_merge_hours = calculate_time_to_merge_hours(pr_created_at, pr_merged_at)

        primary_reviewer = first_review['reviewer']
        first_review_state = first_review['state']
        loc_changed = pr_node.get('additions', 0) + pr_node.get('deletions', 0)
        
        exp_profile = self._fetch_author_experience(repo_name, author_login, pr_created_at)
        
        total_comments = pr_node.get('comments', {}).get('totalCount', human_comments_count)
        total_threads = pr_node.get('reviewThreads', {}).get('totalCount', 0)
        inline_comment_density = round(total_threads / loc_changed, 4) if loc_changed > 0 else 0.0

        return {
            "repository": repo_name,
            "pr_number": pr_node.get('number'),
            "author": author_login,
            "primary_reviewer": primary_reviewer,
            "first_review_latency_hours": round(latency_hours, 2),
            "time_to_merge_hours": round(time_to_merge_hours, 2),
            "first_review_state": first_review_state,
            "inline_comment_density": inline_comment_density,
            "total_discussion_volume": total_comments + len(human_reviews),
            "loc_changed": loc_changed,
            "prior_prs": exp_profile.prior_prs,
            "acceptance_rate": exp_profile.acceptance_rate,
            "formal_reviews": exp_profile.formal_reviews,
            "experience_category": exp_profile.category
        }