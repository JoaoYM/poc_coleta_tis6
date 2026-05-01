import pandas as pd
import numpy as np

def calculate_business_hours_latency(created_at: pd.Timestamp, first_review_at: pd.Timestamp) -> float:
    """Calcula a latência em horas, descontando finais de semana."""
    start_date = created_at.date()
    end_date = first_review_at.date()
    
    business_days = np.busday_count(start_date, end_date)
    total_seconds = (first_review_at - created_at).total_seconds()
    
    calendar_days = (end_date - start_date).days
    weekend_days = calendar_days - business_days
    
    business_seconds_penalty = weekend_days * 86400
    return max(0.0, (total_seconds - business_seconds_penalty) / 3600)

def calculate_time_to_merge_hours(created_at: pd.Timestamp, merged_at: pd.Timestamp) -> float:
    """Calcula o tempo total até o merge em horas."""
    if pd.isna(merged_at):
        return 0.0
    time_to_merge_seconds = (merged_at - created_at).total_seconds()
    return max(0.0, time_to_merge_seconds / 3600)