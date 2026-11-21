"""P1.5 - Exploratory data analysis charts, saved to ml/reports/.

Run from the repo root:  .venv/Scripts/python ml/eda.py
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.features import clean_transactions, history_stats  # noqa: E402

DATA, REPORTS = ROOT / "ml" / "data", ROOT / "ml" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    raw = pd.read_csv(DATA / "transactions.csv")
    tx = clean_transactions(raw)
    vm = pd.read_csv(DATA / "vendor_materials.csv")
    materials = pd.read_csv(DATA / "materials.csv")
    ranking = pd.read_csv(DATA / "ranking_train.csv")

    # 1. on-time rate per vendor
    st = history_stats(tx)
    per_vendor = (st.assign(on_time=st.ontime_rate * st.n_tx).groupby("vendor_id")
                  .agg(on_time=("on_time", "sum"), n=("n_tx", "sum")))
    per_vendor = (per_vendor.on_time / per_vendor.n).sort_values()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(per_vendor.index.astype(str), per_vendor.values * 100, color="#534AB7")
    ax.set(title="On-time delivery rate per vendor (smoothed)", xlabel="vendor id", ylabel="on-time %")
    fig.tight_layout(); fig.savefig(REPORTS / "eda_ontime_by_vendor.png", dpi=120); plt.close(fig)

    # 2. price vs lead time (price normalized per material so materials are comparable)
    vm = vm.merge(materials[["id", "name"]], left_on="material_id", right_on="id", suffixes=("", "_m"))
    vm["price_rel"] = vm.unit_price / vm.groupby("material_id").unit_price.transform("median")
    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(vm.lead_time_days + (vm.vendor_id % 5 - 2) * 0.05, vm.price_rel, c=vm.quality_score,
                    cmap="viridis", alpha=0.8)
    fig.colorbar(sc, label="quality score")
    ax.set(title="Trade-off: relative price vs lead time", xlabel="lead time (days)",
           ylabel="price / material median")
    fig.tight_layout(); fig.savefig(REPORTS / "eda_price_vs_lead.png", dpi=120); plt.close(fig)

    # 3. label distribution
    counts = ranking.label.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(counts.index.astype(str), counts.values, color="#1D9E75")
    ax.set(title="Relevance label distribution (0 = poor, 4 = best)", xlabel="label", ylabel="rows")
    fig.tight_layout(); fig.savefig(REPORTS / "eda_label_distribution.png", dpi=120); plt.close(fig)

    # 4. cleaning before / after
    before = {"rows": len(raw), "missing defect_rate": int(raw.defect_rate.isna().sum()),
              "actual_days > 30": int((raw.actual_days > 30).sum()),
              "duplicates": int(raw.drop(columns="id").duplicated().sum())}
    after = {"rows": len(tx), "missing defect_rate": int(tx.defect_rate.isna().sum()),
             "actual_days > 30": int((tx.actual_days > 30).sum()),
             "duplicates": int(tx.drop(columns="id").duplicated().sum())}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(["before", "after"], [before["rows"], after["rows"]], color=["#888780", "#534AB7"])
    axes[0].set(title="Transaction rows")
    keys = ["missing defect_rate", "actual_days > 30", "duplicates"]
    x = range(len(keys))
    axes[1].bar([i - 0.2 for i in x], [before[k] for k in keys], width=0.4, label="before", color="#888780")
    axes[1].bar([i + 0.2 for i in x], [after[k] for k in keys], width=0.4, label="after", color="#534AB7")
    axes[1].set_xticks(list(x), keys); axes[1].legend(); axes[1].set(title="Data problems")
    fig.tight_layout(); fig.savefig(REPORTS / "eda_cleaning_before_after.png", dpi=120); plt.close(fig)

    print("before cleaning:", before)
    print("after cleaning: ", after)
    print("saved 4 charts to", REPORTS)


if __name__ == "__main__":
    main()
