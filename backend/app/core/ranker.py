"""Loads the trained LightGBM ranker once and scores candidate vendors."""
import json
from functools import lru_cache

import lightgbm as lgb
import numpy as np
import pandas as pd

from app.config import settings
from app.core.features import FEATURE_NAMES, build_candidate_features


class Ranker:
    def __init__(self, artifacts_dir=settings.artifacts_dir):
        names = json.loads((artifacts_dir / "feature_names.json").read_text())
        if names != FEATURE_NAMES:
            raise RuntimeError("feature_names.json does not match app.core.features.FEATURE_NAMES; retrain the model")
        self.booster = lgb.Booster(model_file=str(artifacts_dir / "ranker.txt"))

    def rank(self, req: dict, vm: pd.DataFrame, tx: pd.DataFrame) -> list[dict]:
        """Score every vendor offering req['material_id']; best first, with per-feature contributions."""
        X = build_candidate_features(req, vm, tx)
        if X.empty:
            return []
        scores = self.booster.predict(X[FEATURE_NAMES])
        contrib = self.booster.predict(X[FEATURE_NAMES], pred_contrib=True)[:, :-1]   # last column = bias
        lo, hi = scores.min(), scores.max()
        pct = (scores - lo) / (hi - lo) * 100 if hi > lo else np.full_like(scores, 100.0)
        offers = vm.set_index("vendor_id")
        rows = []
        for i, vendor_id in enumerate(X.index):
            f = X.iloc[i]
            rows.append({
                "vendor_id": int(vendor_id),
                "score": round(float(scores[i]), 4),
                "score_pct": round(float(pct[i]), 1),
                "unit_price": float(f["unit_price_eff"]),
                "total_price": float(f["unit_price_eff"]) * int(req["qty"]),
                "lead_time_days": int(f["lead_typ"]),
                "quality_score": float(f["quality_score"]),
                "ontime_rate": round(float(f["ontime_rate"]), 4),
                "defect_rate": round(float(f["defect_rate"]), 4),
                "n_tx": int(f["n_tx"]),
                "misses_deadline": bool(f["lead_typ"] > req["deadline_days"]),
                "below_moq": bool(f["moq_ratio"] > 1),
                "in_stock": bool(offers.at[vendor_id, "in_stock"]),
                "contributions": {n: round(float(c), 4) for n, c in zip(FEATURE_NAMES, contrib[i])},
            })
        rows.sort(key=lambda r: r["score"], reverse=True)
        for rank, r in enumerate(rows, start=1):
            r["rank"] = rank
        return rows


@lru_cache(maxsize=1)
def get_ranker() -> Ranker:
    return Ranker()


def model_loaded() -> bool:
    try:
        get_ranker()
        return True
    except Exception:
        return False
