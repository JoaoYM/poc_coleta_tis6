import os
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.utils.output_formatter import RepositoryOutputFormatter
from src.models.experience_profile import ExperienceProfile

class ReviewDataExtractor:
    def __init__(self):
        # Configuração de caminhos e variáveis de ambiente
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.query_file = self.base_path / "src" / "infrastructure" / "graphql" / "pr_query.graphql"
        self.output = RepositoryOutputFormatter()
        
        # Carrega o token automaticamente do .env
        load_dotenv(dotenv_path=self.base_path / '.env')
        self.token = os.getenv("GITHUB_TOKEN")
        self.api_url = "https://api.github.com/graphql"
        
        # Cache em memória para evitar consultas duplicadas do mesmo autor na API
        self.experience_cache = {}

    def _get_query_content(self) -> str:
        """Lê o arquivo GraphQL do disco."""
        if not self.query_file.exists():
            raise FileNotFoundError(f"Arquivo de query não encontrado: {self.query_file}")
        return self.query_file.read_text(encoding="utf-8")

    def _is_human(self, author_login: str) -> bool:
        """Filtra bots via sufixo padrão e uma blacklist de ofensores conhecidos."""
        if not author_login:
            return False
            
        login_lower = author_login.lower()
        
        # Filtro 1: Padrão do GitHub
        if login_lower.endswith('[bot]'):
            return False
            
        # Filtro 2: Blacklist de automações famosas do ecossistema Open Source
        known_bots = {
            "dependabot", "dependabot-preview", "renovate", "snyk-bot", 
            "github-actions", "coveralls", "codecov", "greenkeeper", 
            "netlify", "vercel", "sonarcloud", "travis-ci"
        }
        
        return login_lower not in known_bots

    def _get_author_experience(self, repo_name: str, author_login: str, reference_date: datetime) -> ExperienceProfile:
        """
        Calcula a Matriz de Experiência e Impacto Formal com janela de decaimento de 24 meses.
        Utiliza rotina de buscas otimizadas via GraphQL (apenas issueCount).
        """
        cache_key = f"{repo_name}:{author_login}"
        if cache_key in self.experience_cache:
            return self.experience_cache[cache_key]

        # Janela de decaimento: 24 meses antes do PR atual
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

        # repo_name já vem no formato "owner/name" (ex: facebook/react)
        variables = {
            "searchAuthored": f"repo:{repo_name} author:{author_login} is:pr {date_filter}",
            "searchMerged": f"repo:{repo_name} author:{author_login} is:pr is:merged {date_filter}",
            "searchApproved": f"repo:{repo_name} reviewed-by:{author_login} -author:{author_login} review:approved {date_filter}",
            "searchChanges": f"repo:{repo_name} reviewed-by:{author_login} -author:{author_login} review:changes_requested {date_filter}"
        }

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(self.api_url, json={'query': query, 'variables': variables}, headers=headers)
            data = response.json().get('data', {})
            
            prior_prs = data.get('authored', {}).get('issueCount', 0)
            prior_merged = data.get('merged', {}).get('issueCount', 0)
            approved_reviews = data.get('approved', {}).get('issueCount', 0)
            changes_reviews = data.get('changes', {}).get('issueCount', 0)

            formal_reviews = approved_reviews + changes_reviews
            acceptance_rate = (prior_merged / prior_prs) if prior_prs > 0 else 0.0

            # Lógica de Classificação Híbrida (Review Authority > Authoring Quality > Volume)
            if formal_reviews >= 5:
                category = "Core Reviewer"
            elif prior_prs >= 2 and acceptance_rate >= 0.75:
                category = "Reliable Author"
            elif prior_prs >= 2 and acceptance_rate < 0.75:
                category = "Noisy Author"
            else:
                category = "Novice"

            profile = ExperienceProfile(prior_prs, round(acceptance_rate, 2), formal_reviews, category)
            self.experience_cache[cache_key] = profile
            return profile

        except Exception as e:
            print(f"⚠️ Erro ao buscar experiência para {author_login}: {e}")
            # Fallback seguro caso a API falhe para um usuário específico
            return ExperienceProfile(0, 0.0, 0, "Novice")

    def extract_prs_from_csv(self, input_csv: str = "poc_repos_merged_filter.csv", start_date: str = "2026-01-01", end_date: str = "2026-02-28"):
        """Coordena a extração blindada lendo os repositórios aprovados da Fase 1,
        com resiliência de rede, checkpoints em disco e progress bar com ETA."""
        input_path = self.data_dir / input_csv
        output_path = self.data_dir / "poc_prs_extracted.csv"
        
        # Prevenção contra contaminação de dados
        if output_path.exists():
            output_path.unlink()
            print(f"🧹 Arquivo anterior {output_path.name} limpo para nova extração.")

        if not input_path.exists():
            print(f"❌ Erro: Arquivo {input_csv} não encontrado na pasta {self.data_dir}")
            return

        df_repos = pd.read_csv(input_path)
        query_content = self._get_query_content()
        total_repos = len(df_repos)

        self.output.print_fetch_start("GraphQL PR Extractor", total_repos)
        
        # Marca o tempo de início da coleta global
        start_time = time.time()

        for index, row in df_repos.iterrows():
            repo_name = row['name']
            pr_query = f"repo:{repo_name} is:pr is:merged -is:draft merged:{start_date}..{end_date}"
            
            cursor = None
            has_next = True
            repo_prs_data = [] 
            
            # --- CÁLCULO DE TEMPO E ETA ---
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
                
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                
                try:
                    response = requests.post(
                        self.api_url, 
                        json={"query": query_content, "variables": variables}, 
                        headers=headers,
                        timeout=15 
                    )
                    
                    if response.status_code != 200:
                        print(f"❌ Erro na API para {repo_name}: HTTP {response.status_code}")
                        break
                        
                except requests.exceptions.RequestException as e:
                    print(f"🔌 Oscilação de rede detectada: {e}")
                    print("⏳ Aguardando 10 segundos para estabilizar e tentando novamente...")
                    time.sleep(10)
                    continue 
                
                data = response.json()
                
                if 'errors' in data:
                    print(f"❌ Erro GraphQL no repo {repo_name}: {data['errors'][0].get('message', '')}")
                    break
                    
                search_results = data.get('data', {}).get('search', {})
                
                for edge in search_results.get('edges', []):
                    pr_node = edge.get('node')
                    if not pr_node: continue
                    
                    author_data = pr_node.get('author')
                    author_login = author_data.get('login') if author_data else None
                    
                    if not self._is_human(author_login):
                        continue
                        
                    pr_info = self._process_pr_node(repo_name, pr_node, author_login)
                    if pr_info:
                        repo_prs_data.append(pr_info)

                page_info = search_results.get('pageInfo', {})
                has_next = page_info.get('hasNextPage', False)
                cursor = page_info.get('endCursor')
                
                time.sleep(0.5)

            # --- CHECKPOINT DE DISCO (FLUSH DA RAM) ---
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
        """Extrai as métricas de tempo, esforço e perfil de experiência."""
        pr_created_at = pd.to_datetime(pr_node.get('createdAt'))
        
        human_reviews = []
        human_comments_count = 0
        
        for review in pr_node.get('reviews', {}).get('nodes', []):
            if not review or not review.get('author'): continue
            reviewer_login = review['author'].get('login')
            if self._is_human(reviewer_login) and reviewer_login != author_login:
                human_reviews.append({
                    "reviewer": reviewer_login,
                    "date": pd.to_datetime(review['createdAt'])
                })
                
        for comment in pr_node.get('comments', {}).get('nodes', []):
            if not comment or not comment.get('author'): continue
            commenter_login = comment['author'].get('login')
            if self._is_human(commenter_login):
                human_comments_count += 1
                
        if not human_reviews:
            return None
            
        human_reviews.sort(key=lambda x: x['date'])
        first_review_date = human_reviews[0]['date']
        
        # --- Cálculo de Latência (Business Hours) ---
        start_date = pr_created_at.date()
        end_date = first_review_date.date()
        
        business_days = np.busday_count(start_date, end_date)
        total_seconds = (first_review_date - pr_created_at).total_seconds()
        
        calendar_days = (end_date - start_date).days
        weekend_days = calendar_days - business_days
        
        business_seconds_penalty = weekend_days * 86400
        latency_hours = max(0.0, (total_seconds - business_seconds_penalty) / 3600)
        
        primary_reviewer = human_reviews[0]['reviewer']

        # --- Extracao de Novas Variaveis de Controle ---
        # 1. Busca perfil híbrido no cache/API
        exp_profile = self._get_author_experience(repo_name, author_login, pr_created_at)
        
        # 2. Esforço de codificação
        loc_changed = pr_node.get('additions', 0) + pr_node.get('deletions', 0)

        return {
            "repository": repo_name,
            "pr_number": pr_node.get('number'),
            "author": author_login,
            "primary_reviewer": primary_reviewer,
            "first_review_latency_hours": round(latency_hours, 2),
            "discussion_volume": len(human_reviews) + human_comments_count,
            "loc_changed": loc_changed,
            "prior_prs": exp_profile.prior_prs,
            "acceptance_rate": exp_profile.acceptance_rate,
            "formal_reviews": exp_profile.formal_reviews,
            "experience_category": exp_profile.category
        }