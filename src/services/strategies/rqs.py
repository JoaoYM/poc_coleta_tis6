from abc import ABC, abstractmethod
import pandas as pd

class AbstractAnalysisStrategy(ABC):
    """
    Contrato base para todas as análises estatísticas (RQs).
    Garante o Princípio Aberto/Fechado (OCP).
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna o título formatado da RQ."""
        pass

    @abstractmethod
    def execute(self, df: pd.DataFrame) -> None:
        """Executa a lógica da questão de pesquisa sobre o dataset limpo."""
        pass