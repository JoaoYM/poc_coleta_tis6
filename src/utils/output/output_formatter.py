from typing import List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn


class _ProgressUpdater:
    """Classe auxiliar interna para expor métodos de atualização seguros para os Fetchers."""
    def __init__(self, progress_instance: Progress, task_id):
        self._progress = progress_instance
        self._task_id = task_id

    def update_status(self, page: int, total_pages: int):
        self._progress.update(self._task_id, description=f"[cyan]Baixando pág {page}/{total_pages}...")

    def advance_success(self, total_repos: int):
        self._progress.update(self._task_id, advance=1, description=f"[green]Acumulado: {total_repos} repos...")


class RepositoryOutputFormatter:
    
    @staticmethod
    def _format_date_to_brazilian(date_str: str) -> str:
        """Convert ISO date string (YYYY-MM-DD) to Brazilian format (DD/MM/YYYY)"""
        try:
            date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return date_str
    
    @staticmethod
    @contextmanager
    def fetch_progress_context(total_pages: int):
        """Context Manager atualizado para evitar erros de contagem de páginas."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            # Alterado de {task.completed}/{task.total} para apenas o contador de sucessos
            TextColumn("({task.completed} págs processadas)"),
            TimeElapsedColumn()
        ) as progress:
            task = progress.add_task("[cyan]Minerando GitHub API...", total=total_pages)
            yield _ProgressUpdater(progress, task)
            
    @staticmethod
    def print_repositories(repos: List[Dict[str, Any]]) -> None:
        console = Console()
        
        console.print(f"\n🎯 REPOSITÓRIOS COLETADOS - TOTAL: {len(repos)}", 
                     style="bold cyan")
        
        table = Table(title="Detalhes dos Repositórios (POC)", box=box.ROUNDED, 
                     show_lines=True, header_style="bold magenta")
        
        table.add_column("Nº", justify="center", style="dim")
        table.add_column("Nome", style="cyan", no_wrap=False, overflow="fold")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Criado", justify="center", style="dim")
        table.add_column("Último Push", justify="center", style="dim")
        table.add_column("PRs (Merged)", justify="right", style="green")
        table.add_column("Devs", justify="right", style="magenta")
        
        for i, repo in enumerate(repos, 1):
            table.add_row(
                str(i),
                repo.get('name', 'N/A'),
                f"{repo.get('stargazerCount', 0):,}",
                RepositoryOutputFormatter._format_date_to_brazilian(repo.get('createdAt', '')),
                RepositoryOutputFormatter._format_date_to_brazilian(repo.get('pushedAt', '')),
                f"{repo.get('total_prs', 0):,}",
                f"{repo.get('contributor_count', 0):,}"
            )
        
        console.print(table)
    
    @staticmethod
    def print_summary(repos: List[Dict[str, Any]]) -> None:
        console = Console()
        
        total_stars = sum(repo.get('stargazerCount', 0) for repo in repos)
        total_prs = sum(repo.get('total_prs', 0) for repo in repos)
        
        stats_table = Table(title="📊 Totais Gerais (POC)", box=box.ROUNDED,
                           header_style="bold cyan")
        stats_table.add_column("Métrica", style="cyan")
        stats_table.add_column("Valor", justify="right", style="yellow")
        
        stats_table.add_row("Estrelas Acumuladas", f"{total_stars:,}")
        stats_table.add_row("Pull Requests (Merged)", f"{total_prs:,}")
        
        console.print(stats_table)
    
    @staticmethod
    def print_fetch_start(method: str, pages: int, max_repos: int = 0) -> None:
        console = Console()
        if max_repos > 0:
            console.print(f"🚀 Iniciando coleta de {max_repos} repositórios ({pages} páginas estimadas)...", 
                          style="bold yellow")
        else:
            console.print(f"🚀 Iniciando coleta (Estimativa: {pages} páginas)...", 
                          style="bold yellow")
        console.print(f"📡 Método de Busca: {method}", style="cyan")
    
    @staticmethod
    def print_no_repos() -> None:
        console = Console()
        console.print("❌ Nenhum repositório foi coletado!", style="bold red")
    
    @staticmethod
    def print_save_success(filepath: str) -> None:
        console = Console()
        console.print(f"\n✅ Dados salvos em {filepath}", style="bold green")
    
    @staticmethod
    def print_json_hint() -> None:
        console = Console()
        console.print("\nℹ️  Use --json para salvar os dados em JSON", style="cyan")
    
    @staticmethod
    def print_error(error: str) -> None:
        console = Console()
        console.print(f"❌ {error}", style="bold red")
    
    @staticmethod
    def print_completion(count: int) -> None:
        console = Console()
        console.print(f"\n🎉 Processo concluído! {count} repositórios processados.", 
                     style="bold green")