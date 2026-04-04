import os
import subprocess
import shutil
import csv
from pathlib import Path
import pandas as pd
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

class MetricsCollector:
    def __init__(self, ck_jar_path: str = "ck.jar"):
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.temp_clone_dir = self.base_path / "temp_repos"
        self.ck_jar_path = self.base_path / ck_jar_path
        self.input_csv = self.data_dir / 'repos.csv'
        self.output_csv = self.data_dir / 'ck_metrics_consolidated.csv'
        
    def _get_processed_repos(self) -> set:
        """Lê o arquivo de saída para descobrir quais repositórios já foram processados."""
        if not self.output_csv.exists():
            return set()
        
        try:
            df = pd.read_csv(self.output_csv)
            return set(df['name'].tolist())
        except pd.errors.EmptyDataError:
            return set()

    def _summarize_ck_metrics(self, repo_name: str, ck_out_dir: Path) -> dict:
        """Lê o class.csv gerado pelo CK e calcula média, mediana e desvio padrão."""
        class_csv = ck_out_dir / "class.csv"
        
        if not class_csv.exists():
            raise FileNotFoundError("O arquivo class.csv não foi gerado pelo CK.")
            
        df = pd.read_csv(class_csv)
        
        # Se o repositório não tiver classes, retorna zeros
        if df.empty:
            return {col: 0 for col in ['cbo_mean', 'cbo_median', 'cbo_std', 'dit_mean', 'dit_median', 'dit_std', 'lcom_mean', 'lcom_median', 'lcom_std', 'loc_mean', 'loc_median', 'loc_std', 'loc_total']}

        metrics = {}
        for metric in ['cbo', 'dit', 'lcom', 'loc']:
            # LCOM vem como 'lcom' ou 'lcom*' dependendo da versão do CK, pegamos a padrão
            col_name = metric if metric in df.columns else f"{metric}*" if f"{metric}*" in df.columns else metric
            
            if col_name in df.columns:
                metrics[f'{metric}_mean'] = df[col_name].mean()
                metrics[f'{metric}_median'] = df[col_name].median()
                metrics[f'{metric}_std'] = df[col_name].std()
            else:
                metrics[f'{metric}_mean'] = 0
                metrics[f'{metric}_median'] = 0
                metrics[f'{metric}_std'] = 0
                
        # Total de LOC do repositório (soma das classes)
        metrics['loc_total'] = df['loc'].sum() if 'loc' in df.columns else 0
        
        return metrics

    def _force_delete(self, path_to_delete: Path):
        """Força a deleção de pastas no Windows lidando com arquivos Read-Only do .git"""
        if not path_to_delete.exists():
            return
            
        # 1. Tenta alterar as permissões de todos os arquivos para leitura/escrita
        import stat
        for root, dirs, files in os.walk(path_to_delete):
            for dir_name in dirs:
                os.chmod(os.path.join(root, dir_name), stat.S_IWRITE)
            for file_name in files:
                os.chmod(os.path.join(root, file_name), stat.S_IWRITE)
                
        # 2. Tenta deletar com o Python
        shutil.rmtree(path_to_delete, ignore_errors=True)
        
        # 3. Se ainda assim sobrar sujeira (muito comum no Windows), usa o comando nativo do CMD
        if path_to_delete.exists() and os.name == 'nt':
            subprocess.run(['rmdir', '/S', '/Q', str(path_to_delete)], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def process_all_repositories(self):
        """Inicia o processamento em lote com resume e barra de progresso."""
        if not self.input_csv.exists():
            print("❌ Arquivo repos.csv não encontrado. Rode a coleta primeiro.")
            return

        # Lê a lista de repositórios coletados (com Pandas para pegar as outras colunas fáceis)
        input_df = pd.read_csv(self.input_csv)
        total_repos = len(input_df)
        
        processed_names = self._get_processed_repos()
        repos_to_process = input_df[~input_df['name'].isin(processed_names)]
        
        if repos_to_process.empty:
            print("✅ Todos os repositórios já foram processados!")
            return

        # Prepara o arquivo de saída (escreve cabeçalho se não existir)
        is_new_file = not self.output_csv.exists()
        
        print(f"\n🚀 Retomando/Iniciando processamento. Faltam {len(repos_to_process)} de {total_repos} repositórios.\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn()
        ) as progress:
            
            task = progress.add_task("[cyan]Processando...", total=total_repos, completed=len(processed_names))
            
            # Abre o arquivo em modo 'append' para ir salvando um por um
            with open(self.output_csv, 'a', newline='', encoding='utf-8') as f:
                writer = None
                
                for index, row in repos_to_process.iterrows():
                    repo_name = row['name']
                    repo_url = row['url']
                    
                    progress.update(task, description=f"[cyan]Clonando: [bold]{repo_name}[/bold]")
                    
                    repo_path = self.temp_clone_dir / repo_name.replace("/", "_")
                    ck_out_dir = self.data_dir / "ck_results" / repo_name.replace("/", "_")
                    
                    if repo_path.exists():
                        self._force_delete(repo_path)
                        
                    try:
                        # 1. Clone otimizado
                        subprocess.run(["git", "clone", "--depth", "1", "--single-branch", repo_url, str(repo_path)], 
                                     check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        # 2. Execução do CK
                        progress.update(task, description=f"[magenta]Analisando CK: [bold]{repo_name}[/bold]")
                        ck_out_dir.mkdir(parents=True, exist_ok=True)
                        subprocess.run([
                            "java", "-Xmx4g", "-jar", str(self.ck_jar_path),
                            str(repo_path), "true", "0", "False", str(ck_out_dir)
                        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        # 3. Sumarização dos Dados
                        progress.update(task, description=f"[green]Sumarizando: [bold]{repo_name}[/bold]")
                        metrics_summary = self._summarize_ck_metrics(repo_name, ck_out_dir)
                        
                        # 4. Mescla os dados da API com as métricas do CK
                        final_row = row.to_dict()
                        final_row.update(metrics_summary)
                        
                        # Configura o CSV Writer dinamicamente
                        if is_new_file:
                            writer = csv.DictWriter(f, fieldnames=final_row.keys())
                            writer.writeheader()
                            is_new_file = False
                        elif writer is None:
                            writer = csv.DictWriter(f, fieldnames=final_row.keys())
                            
                        # Salva o repositório atual
                        writer.writerow(final_row)
                        f.flush() # Força a escrita no disco
                        
                    except Exception as e:
                        # Em vez de travar o script inteiro, loga o erro e pula pro próximo
                        progress.console.print(f"[red]❌ Erro no repositório {repo_name}: {str(e)[:100]}[/red]")
                    finally:
                        # Limpeza Blindada (apaga o clone e o CSV bruto do CK)
                        self._force_delete(repo_path)
                        self._force_delete(ck_out_dir)
                        progress.update(task, advance=1)