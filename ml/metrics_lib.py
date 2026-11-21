"""Ranking metrics shared by training and evaluation scripts."""
import numpy as np
import pandas as pd
from scipy.stats import kendalltau


def ndcg_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int) -> float:
    """NDCG@k with gain 2^rel - 1 and log2(position + 1) discount (LightGBM's default)."""
    order = np.argsort(-y_score, kind="stable")[:k]
    ideal = np.sort(y_true)[::-1][:k]
    disc = 1 / np.log2(np.arange(2, k + 2))
    dcg = ((2 ** y_true[order] - 1) * disc[:len(order)]).sum()
    idcg = ((2 ** ideal - 1) * disc[:len(ideal)]).sum()
    return float(dcg / idcg) if idcg > 0 else 1.0


def evaluate_scores(df: pd.DataFrame, score_col: str) -> dict:
    """Average NDCG@1/3/5 and Kendall tau over requests (one group = one request)."""
    res = {"ndcg@1": [], "ndcg@3": [], "ndcg@5": [], "kendall_tau": []}
    for _, g in df.groupby("request_id"):
        y, s = g["label"].to_numpy(), g[score_col].to_numpy()
        for k in (1, 3, 5):
            res[f"ndcg@{k}"].append(ndcg_at_k(y, s, k))
        tau = kendalltau(y, s).statistic
        if not np.isnan(tau):
            res["kendall_tau"].append(tau)
    return {k: round(float(np.mean(v)), 4) for k, v in res.items()}
