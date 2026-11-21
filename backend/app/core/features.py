"""Preprocessing and feature building.

This is the ONE place features are computed. The training scripts (ml/) and the
running app both import it, so the model always sees features computed the same way
(no "training/serving skew").
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Order matters: the saved model expects exactly this column order.
FEATURE_NAMES = [
    # describe the request (lets the model adapt to the user's priorities)
    "deadline_days", "log_qty", "w_price", "w_speed", "w_quality",
    # describe the vendor offer for this request
    "unit_price_eff", "price_rel_median", "lead_typ", "slack_typ", "lead_p90", "slack_p90",
    "quality_score", "ontime_rate", "defect_rate", "moq_ratio", "in_stock", "n_tx",
]

MAX_PLAUSIBLE_DAYS = 30   # delivery longer than this is treated as a data-entry error
ONTIME_PRIOR = 0.85       # prior on-time rate for vendors with little history
PRIOR_WEIGHT = 3          # how many "virtual" transactions the prior is worth

TX_COLUMNS = ["vendor_id", "material_id", "qty", "unit_price", "ordered_at",
              "promised_days", "actual_days", "defect_rate"]


def clean_transactions(tx: pd.DataFrame) -> pd.DataFrame:
    """Fix the known data problems in transaction history.

    1. duplicated entries (same order typed twice, different id) -> keep one
    2. impossible delivery times (> 30 days)                       -> drop the row
    3. missing defect rate                                          -> vendor median, else global median
    """
    tx = tx.copy()
    if tx.empty:
        return tx
    tx = tx.drop_duplicates(subset=[c for c in TX_COLUMNS if c in tx.columns])
    tx = tx[tx["actual_days"] <= MAX_PLAUSIBLE_DAYS]
    vendor_median = tx.groupby("vendor_id")["defect_rate"].transform("median")
    tx["defect_rate"] = tx["defect_rate"].fillna(vendor_median).fillna(tx["defect_rate"].median()).fillna(0.0)
    for c in ("vendor_id", "material_id", "qty", "promised_days", "actual_days"):
        tx[c] = tx[c].astype(int)
    tx["unit_price"] = tx["unit_price"].astype(float)
    tx["defect_rate"] = tx["defect_rate"].astype(float)
    return tx.reset_index(drop=True)


def effective_price(row: pd.Series, qty: int) -> float:
    """Bulk price applies once the order reaches bulk_min_qty."""
    bulk_min = row.get("bulk_min_qty")
    if pd.notna(bulk_min) and pd.notna(row.get("bulk_unit_price")) and qty >= bulk_min:
        return float(row["bulk_unit_price"])
    return float(row["unit_price"])


def history_stats(tx: pd.DataFrame) -> pd.DataFrame:
    """Per vendor-material history: count, on-time rate, p90 delivery days, defect rate."""
    if tx.empty:
        return pd.DataFrame(columns=["vendor_id", "material_id", "n_tx", "ontime_rate", "lead_p90", "defect_rate"])
    g = tx.assign(on_time=(tx["actual_days"] <= tx["promised_days"]).astype(int)).groupby(["vendor_id", "material_id"])
    stats = g.agg(n_tx=("on_time", "size"), on_time=("on_time", "sum"),
                  lead_p90=("actual_days", lambda s: float(np.percentile(s, 90))),
                  defect_rate=("defect_rate", "mean")).reset_index()
    stats["ontime_rate"] = (stats["on_time"] + ONTIME_PRIOR * PRIOR_WEIGHT) / (stats["n_tx"] + PRIOR_WEIGHT)
    return stats.drop(columns="on_time")


def build_candidate_features(req: dict, vm: pd.DataFrame, tx: pd.DataFrame,
                             stats: pd.DataFrame | None = None) -> pd.DataFrame:
    """Feature table for every vendor offering req['material_id'].

    req: material_id, qty, deadline_days, w_price, w_speed, w_quality
    vm:  vendor_materials rows (any materials; filtered here)
    tx:  CLEANED transactions (any materials; filtered here)
    stats: optional precomputed history_stats(tx) for speed during training
    Returns a DataFrame indexed by vendor_id with columns FEATURE_NAMES.
    """
    qty = int(req["qty"])
    deadline = float(req["deadline_days"])
    cand = vm[vm["material_id"] == req["material_id"]].copy()
    if cand.empty:
        return pd.DataFrame(columns=FEATURE_NAMES)

    if stats is None:
        stats = history_stats(tx[tx["material_id"] == req["material_id"]])
    hist = stats[stats["material_id"] == req["material_id"]].set_index("vendor_id")

    cand["unit_price_eff"] = cand.apply(lambda r: effective_price(r, qty), axis=1)
    cand = cand.set_index("vendor_id")
    out = pd.DataFrame(index=cand.index)
    out["deadline_days"] = deadline
    out["log_qty"] = np.log1p(qty)
    out["w_price"] = float(req["w_price"])
    out["w_speed"] = float(req["w_speed"])
    out["w_quality"] = float(req["w_quality"])
    out["unit_price_eff"] = cand["unit_price_eff"]
    out["price_rel_median"] = cand["unit_price_eff"] / cand["unit_price_eff"].median()
    out["lead_typ"] = cand["lead_time_days"].astype(float)
    out["slack_typ"] = deadline - out["lead_typ"]
    out["lead_p90"] = hist["lead_p90"].reindex(out.index).fillna(out["lead_typ"] * 1.3)
    out["slack_p90"] = deadline - out["lead_p90"]
    out["quality_score"] = cand["quality_score"].astype(float)
    out["ontime_rate"] = hist["ontime_rate"].reindex(out.index).fillna(ONTIME_PRIOR)
    out["defect_rate"] = hist["defect_rate"].reindex(out.index).fillna(
        stats["defect_rate"].median() if len(stats) else 0.03)
    out["moq_ratio"] = cand["moq"].astype(float) / qty
    out["in_stock"] = cand["in_stock"].astype(bool).astype(float)
    out["n_tx"] = hist["n_tx"].reindex(out.index).fillna(0).astype(float)
    return out[FEATURE_NAMES]
