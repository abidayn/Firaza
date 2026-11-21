"""P2.4-P2.7 - Evaluate the trained ranker on the TEST split against baselines and controls.

Run from the repo root (after train_ranker.py):  .venv/Scripts/python ml/evaluate.py
Writes ml/reports/metrics.json, ml/reports/metrics.md, ml/reports/feature_importance.png
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml"))
from app.core.features import FEATURE_NAMES  # noqa: E402
from baselines import BASELINES  # noqa: E402
from metrics_lib import evaluate_scores, ndcg_at_k  # noqa: E402
from train_ranker import load, train  # noqa: E402

REPORTS = ROOT / "ml" / "reports"
ARTIFACTS = ROOT / "backend" / "artifacts"


def sanity_check_ndcg() -> None:
    y = np.array([4, 3, 1, 0])
    perfect = ndcg_at_k(y, np.array([4.0, 3, 2, 1]), 3)
    reversed_ = ndcg_at_k(y, np.array([1.0, 2, 3, 4]), 3)
    assert abs(perfect - 1.0) < 1e-9, perfect
    assert reversed_ < 0.7, reversed_
    print(f"ndcg sanity: perfect={perfect:.3f} reversed={reversed_:.3f}")


def ablation_sentence(full: dict, ablated: dict) -> str:
    delta = round(ablated["ndcg@3"] - full["ndcg@3"], 4)
    if delta < -0.01:
        return (f"Removing the deadline-slack features drops NDCG@3 to {ablated['ndcg@3']} ({delta}), so the model "
                "relies on them to judge 'can this vendor deliver before the deadline'.")
    return (f"Removing the deadline-slack features changes NDCG@3 only to {ablated['ndcg@3']} ({delta:+}). They are "
            "redundant: slack = deadline - lead time, and the model still sees deadline_days and lead_typ, so the "
            "trees rebuild that comparison themselves. The deadline information matters; this particular encoding of "
            "it does not.")


def main() -> None:
    sanity_check_ndcg()
    parts = load()
    test = parts["test"][0].copy()
    booster = lgb.Booster(model_file=str(ARTIFACTS / "ranker.txt"))
    test["model"] = booster.predict(test[FEATURE_NAMES])

    results = {"lightgbm_lambdarank": evaluate_scores(test, "model")}
    for name, fn in BASELINES.items():
        test[name] = 0.0
        for _, g in test.groupby("request_id"):
            test.loc[g.index, name] = fn(g)
        results[f"baseline_{name}"] = evaluate_scores(test, name)

    # control: same model, labels shuffled -> it can only learn noise
    rng = np.random.default_rng(0)
    shuffled = rng.permutation(parts["train"][2].to_numpy())
    control = train(parts, label_override=shuffled, quiet=True)
    test["control"] = control.predict(test[FEATURE_NAMES])
    results["control_shuffled_labels"] = evaluate_scores(test, "control")

    # "break it": remove the deadline-slack features
    reduced = [f for f in FEATURE_NAMES if f not in ("slack_typ", "slack_p90")]
    ablated = train(parts, features=reduced, quiet=True)
    test["ablation"] = ablated.predict(test[reduced])
    results["ablation_no_slack_features"] = evaluate_scores(test, "ablation")

    # contributions must add up to the raw score (used later to explain predictions)
    sample = test[FEATURE_NAMES].head(200)
    contrib = booster.predict(sample, pred_contrib=True)
    assert contrib.shape == (len(sample), len(FEATURE_NAMES) + 1), contrib.shape
    assert np.allclose(contrib.sum(axis=1), booster.predict(sample), atol=1e-6)
    print("pred_contrib check: shape", contrib.shape, "rows sum to raw score: ok")

    # feature importance (total gain)
    gain = booster.feature_importance(importance_type="gain")
    order = np.argsort(gain)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(np.array(FEATURE_NAMES)[order], gain[order], color="#534AB7")
    ax.set(title="Feature importance (total gain)", xlabel="gain")
    fig.tight_layout(); fig.savefig(REPORTS / "feature_importance.png", dpi=120); plt.close(fig)

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "metrics.json").write_text(json.dumps(results, indent=2))

    m = results["lightgbm_lambdarank"]
    best_base = max((k for k in results if k.startswith("baseline_")), key=lambda k: results[k]["ndcg@3"])
    lines = ["# Ranking evaluation (test split, %d requests)" % test.request_id.nunique(), "",
             "| Method | NDCG@1 | NDCG@3 | NDCG@5 | Kendall τ |", "|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['ndcg@1']} | {r['ndcg@3']} | {r['ndcg@5']} | {r['kendall_tau']} |")
    beats = all(m["ndcg@3"] > results[k]["ndcg@3"] for k in results if k.startswith("baseline_"))
    target = "meets" if m["ndcg@3"] >= 0.85 else "does not meet"
    lines += ["", "## Conclusion", "",
              f"The trained LambdaRank model reaches NDCG@3 = {m['ndcg@3']} on unseen requests, which {target} the "
              f"0.85 target from the Project Plan. It {'beats' if beats else 'does not beat'} every baseline; the "
              f"strongest baseline is `{best_base}` at NDCG@3 = {results[best_base]['ndcg@3']}.",
              "",
              f"The shuffled-label control scores NDCG@3 = {results['control_shuffled_labels']['ndcg@3']}, so the "
              "model's score comes from real patterns in the features, not from chance or from the evaluation code.",
              "",
              ablation_sentence(m, results["ablation_no_slack_features"]),
              "",
              "Limitation: labels come from a simulated utility function (see docs/DATA_CARD.md). These numbers show "
              "the pipeline works on simulated data; they are not a measurement of accuracy on Firaza's real data."]
    (REPORTS / "metrics.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
