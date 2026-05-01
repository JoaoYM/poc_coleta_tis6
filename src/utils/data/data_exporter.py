import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from src.utils.output.output_formatter import RepositoryOutputFormatter

class DataExporter:
    """
    Especialista em I/O de disco.
    Isola a responsabilidade de manipulação de diretórios e salvamento de arquivos.
    """
    def __init__(self):
        # Resolve o caminho dinamicamente para a raiz do projeto
        self.base_path = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_path / "data"
        self.output = RepositoryOutputFormatter()

    def save_csv(self, data: List[Dict[str, Any]], filename: str) -> None:
        """Salva a lista de dicionários em um arquivo CSV usando Pandas."""
        if not data:
            return
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.data_dir / filename
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        self.output.print_save_success(str(output_path))

    def save_json(self, data: List[Dict[str, Any]], filename: str) -> None:
        """Salva a lista de dicionários em um arquivo JSON nativo."""
        if not data:
            return
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.data_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        self.output.print_save_success(str(output_path))