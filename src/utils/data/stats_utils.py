import pandas as pd
import numpy as np

def cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calcula o tamanho do efeito (Cohen's d) entre dois grupos."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0: 
        return 0.0
    
    var1, var2 = group1.var(), group2.var()
    # Desvio padrão agrupado (pooled standard deviation)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0: 
        return 0.0
    return (group1.mean() - group2.mean()) / pooled_std