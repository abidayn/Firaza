"""P2.3 - Train the LightGBM LambdaRank vendor ranker.

Run from the repo root:  .venv/Scripts/python ml/train_ranker.py
Saves backend/artifacts/ranker.txt and backend/artifacts/feature_names.json
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.features import FEATURE_NAMES  # noqa: E402

DATA = ROOT / "ml" / "data"
ARTIFACTS = ROOT / "backend" / "artifacts"

PARAMS = dict(objective="lambdarank", n_estimators=500, learning_rate=0.05, num_leaves=15,
              min_child_samples=20, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
              random_state=42, verbose=-1)


def load(features=FEATURE_NAMES):
    df = pd.read_csv(DATA / "ranking_train.csv").sort_values(["request_id", "vendor_id"])
    parts = {}
    for name in ("train", "val", "test"):
        d = df[df["split"] == name]
        parts[name] = (d, d[features], d["label"], d.groupby("request_id", sort=True).size().to_numpy())
    return parts


def train(parts, features=FEATURE_NAMES, label_override=None, quiet=False) -> lgb.LGBMRanker:
    _, Xtr, ytr, gtr = parts["train"]
    _, Xva, yva, gva = parts["val"]
    if label_override is not None:
        ytr = label_override
    model = lgb.LGBMRanker(**PARAMS)
    model.fit(Xtr[features], ytr, group=gtr,
              eval_set=[(Xva[features], yva)], eval_group=[gva], eval_at=[1, 3, 5],
              callbacks=[lgb.early_stopping(30, verbose=False)] + ([] if quiet else [lgb.log_evaluation(50)]))
    return model


def main() -> None:
    parts = load()
    model = train(parts)
    best = model.best_score_["valid_0"]
    print(f"best iteration: {model.best_iteration_}")
    print("validation:", {k: round(v, 4) for k, v in best.items()})
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(ARTIFACTS / "ranker.txt"), num_iteration=model.best_iteration_)
    (ARTIFACTS / "feature_names.json").write_text(json.dumps(FEATURE_NAMES, indent=2))
    print("saved", ARTIFACTS / "ranker.txt")


if __name__ == "__main__":
    main()
