"""
DataFrame Construction Utilities

Provides helpers for common DataFrame creation patterns used in evaluation notebooks.
Reduces boilerplate and ensures consistent data structure handling.

Used by:
- 01c_extraction_evaluation.ipynb
- 01d_comparative_evaluation.ipynb
"""

import pandas as pd
from typing import Any, Callable


def results_to_dataframe(
    results: list[dict],
    column_mapping: dict[str, str] | None = None,
    round_columns: dict[str, int] | None = None
) -> pd.DataFrame:
    """
    Convert list of result dicts to DataFrame with optional column renaming and rounding.
    
    Args:
        results: List of dictionaries with evaluation results
        column_mapping: Optional dict mapping result keys to DataFrame column names
        round_columns: Optional dict mapping column names to decimal places
    
    Returns:
        DataFrame with results
    """
    if not results:
        return pd.DataFrame()
    
    # Build data for DataFrame
    data = []
    for result in results:
        row = {}
        for key, value in result.items():
            # Use mapped column name or original key
            col_name = column_mapping.get(key, key) if column_mapping else key
            row[col_name] = value
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Apply rounding
    if round_columns:
        for col, decimals in round_columns.items():
            if col in df.columns:
                df[col] = df[col].round(decimals)
    
    return df


def aggregate_page_results(
    pages: list[dict],
    metric_extractor: Callable[[dict], dict],
    aggregation_funcs: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Aggregate metrics across multiple pages.
    
    Args:
        pages: List of page result dicts
        metric_extractor: Function to extract metrics from a page dict
        aggregation_funcs: Dict mapping metric names to aggregation functions
                          ('sum', 'mean', 'count', 'min', 'max')
                          Default: all metrics use 'sum'
    
    Returns:
        Dict with aggregated metrics
    """
    if not pages:
        return {}
    
    # Extract metrics from all pages
    all_metrics = [metric_extractor(page) for page in pages]
    
    # Get all metric names
    metric_names = set()
    for metrics in all_metrics:
        metric_names.update(metrics.keys())
    
    # Default to sum for all metrics
    if aggregation_funcs is None:
        aggregation_funcs = {name: 'sum' for name in metric_names}
    
    # Aggregate
    aggregated = {}
    for metric_name in metric_names:
        values = [m.get(metric_name, 0) for m in all_metrics]
        
        agg_func = aggregation_funcs.get(metric_name, 'sum')
        
        if agg_func == 'sum':
            aggregated[metric_name] = sum(values)
        elif agg_func == 'mean':
            aggregated[metric_name] = sum(values) / len(values) if values else 0
        elif agg_func == 'count':
            aggregated[metric_name] = len(values)
        elif agg_func == 'min':
            aggregated[metric_name] = min(values) if values else 0
        elif agg_func == 'max':
            aggregated[metric_name] = max(values) if values else 0
        else:
            raise ValueError(f"Unknown aggregation function: {agg_func}")
    
    return aggregated


def merge_evaluation_results(*result_dicts: dict) -> dict:
    """
    Merge multiple evaluation result dictionaries.
    
    Combines results from different evaluation dimensions into a single summary.
    
    Args:
        *result_dicts: Variable number of result dictionaries to merge
    
    Returns:
        Merged dictionary (later dicts override earlier ones)
    """
    merged = {}
    for result_dict in result_dicts:
        merged.update(result_dict)
    return merged