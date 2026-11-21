"""P2.1 - Simple ranking methods the trained model must beat.

Each function takes one request's candidate rows (the same feature table the model sees)
and returns one score per row: higher = better.
"""
import numpy as np
import pandas as pd


def _minmax(x: np.ndarray) -> np.ndarray:
    span = x.max() - x.min()
    return (x - x.min()) / span if span > 0 else np.ones_like(x, dtype=float)


def cheapest(c: pd.DataFrame) -> np.ndarray:
    """Lowest effective unit price first."""
    return -c["unit_price_eff"].to_numpy(dtype=float)


def weighted_sum(c: pd.DataFrame) -> np.ndarray:
    """The 'spreadsheet formula': user weights x normalized price, speed, quality (linear)."""
    w = c.iloc[0][["w_price", "w_speed", "w_quality"]].to_numpy(dtype=float)
    price_s = 1 - _minmax(c["unit_price_eff"].to_numpy(dtype=float))
    lead = c["lead_typ"].to_numpy(dtype=float)
    speed_s = 1 - lead / lead.max()
    qual_s = (c["quality_score"].to_numpy(dtype=float) - 1) / 4
    return w[0] * price_s + w[1] * speed_s + w[2] * qual_s


def topsis(c: pd.DataFrame) -> np.ndarray:
    """TOPSIS: closeness to the ideal option across criteria (Hwang & Yoon, 1981).

    Criteria: price (cost), lead time (cost), quality (benefit), on-time rate (benefit).
    The speed weight is split equally between lead time and on-time rate.
    """
    w0 = c.iloc[0][["w_price", "w_speed", "w_quality"]].to_numpy(dtype=float)
    weights = np.array([w0[0], w0[1] / 2, w0[2], w0[1] / 2])
    m = c[["unit_price_eff", "lead_typ", "quality_score", "ontime_rate"]].to_numpy(dtype=float)
    norm = np.sqrt((m ** 2).sum(axis=0))
    norm[norm == 0] = 1
    v = m / norm * weights
    benefit = np.array([False, False, True, True])
    ideal = np.where(benefit, v.max(axis=0), v.min(axis=0))
    worst = np.where(benefit, v.min(axis=0), v.max(axis=0))
    d_ideal = np.sqrt(((v - ideal) ** 2).sum(axis=1))
    d_worst = np.sqrt(((v - worst) ** 2).sum(axis=1))
    denom = d_ideal + d_worst
    return np.where(denom > 0, d_worst / np.where(denom > 0, denom, 1), 0.5)


BASELINES = {"cheapest": cheapest, "weighted_sum": weighted_sum, "topsis": topsis}
