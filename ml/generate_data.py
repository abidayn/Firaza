"""P1.1 - Generate the synthetic Firaza procurement dataset.

Creates, under ml/data/:
  materials.csv, vendors.csv, vendor_materials.csv, transactions.csv  (what the app/DB sees)
  _latent/vendor_truth.csv                                            (hidden truth, labels only)

Run from the repo root:  .venv/Scripts/python ml/generate_data.py
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
rng = np.random.default_rng(SEED)
fake = Faker("id_ID")
Faker.seed(SEED)

OUT = Path(__file__).resolve().parent / "data"
LATENT = OUT / "_latent"
OUT.mkdir(parents=True, exist_ok=True)
LATENT.mkdir(parents=True, exist_ok=True)

# name, category, unit, base price (Rp per unit), base lead time (days)
MATERIALS = [
    ("Kardus 30x20x15 cm", "packaging", "pcs", 2100, 2),
    ("Kardus 40x30x20 cm", "packaging", "pcs", 3400, 2),
    ("Pita satin 2 cm", "ribbon", "meter", 900, 2),
    ("Pita grosgrain", "ribbon", "meter", 1300, 3),
    ("Plastik bubble wrap", "packaging", "meter", 2500, 2),
    ("Polymailer 25x35 cm", "packaging", "pcs", 700, 2),
    ("Kotak hampers premium", "packaging", "pcs", 18000, 4),
    ("Kertas kado", "packaging", "lembar", 1500, 2),
    ("Benang bordir", "embroidery_printing", "gulung", 6500, 3),
    ("Label stiker custom", "embroidery_printing", "lembar", 400, 3),
    ("Tali rafia", "packaging", "gulung", 8000, 1),
    ("Lakban bening 2 inch", "packaging", "gulung", 9500, 1),
]
CITIES = ["Bandung", "Jakarta", "Surabaya", "Semarang", "Tangerang", "Bekasi", "Solo", "Yogyakarta"]
PREFIX = ["CV", "PT", "UD", "Toko"]
WORDS = ["Kemasan", "Packindo", "Sinar", "Mitra", "Karya", "Berkah", "Prima", "Sentosa", "Abadi", "Makmur",
         "Jaya", "Indah", "Mulia", "Utama", "Lestari", "Sejahtera"]
N_VENDORS = 32


def make_materials() -> pd.DataFrame:
    return pd.DataFrame(
        [{"id": i + 1, "name": n, "category": c, "unit": u} for i, (n, c, u, _, _) in enumerate(MATERIALS)]
    )


def make_vendors() -> tuple[pd.DataFrame, pd.DataFrame]:
    names, rows, truth = set(), [], []
    while len(names) < N_VENDORS:
        a, b = rng.choice(WORDS, 2, replace=False)
        names.add(f"{rng.choice(PREFIX)} {a} {b}")
    for i, name in enumerate(sorted(names)):
        vid = i + 1
        rows.append({"id": vid, "name": name, "city": rng.choice(CITIES),
                     "notes": f"Kontak: {fake.first_name()} (sales)"})
        truth.append({
            "vendor_id": vid,
            "reliability_true": float(np.clip(rng.beta(8, 2), 0.6, 0.99)),
            "quality_true": float(np.clip(rng.normal(3.8, 0.5), 2.5, 5.0)),
            "speed_factor": float(rng.uniform(0.6, 1.6)),
            # slightly pricier vendors tend to have better quality
            "price_factor": 0.0,
        })
    truth = pd.DataFrame(truth)
    truth["price_factor"] = np.clip(
        1.0 + 0.08 * (truth["quality_true"] - 3.8) + rng.normal(0, 0.10, len(truth)), 0.75, 1.35)
    return pd.DataFrame(rows), truth


def make_vendor_materials(truth: pd.DataFrame) -> pd.DataFrame:
    n_mat = len(MATERIALS)
    supplies = {v: set(rng.choice(n_mat, rng.integers(4, 8), replace=False) + 1) for v in truth["vendor_id"]}
    # guarantee every material has at least 5 vendors
    for m in range(1, n_mat + 1):
        holders = [v for v, s in supplies.items() if m in s]
        while len(holders) < 5:
            v = int(rng.choice([v for v in supplies if v not in holders]))
            supplies[v].add(m)
            holders.append(v)

    rows, vm_id = [], 1
    t = truth.set_index("vendor_id")
    for v in sorted(supplies):
        for m in sorted(supplies[v]):
            _, _, _, base_price, base_lead = MATERIALS[m - 1]
            price = round(base_price * t.at[v, "price_factor"] * rng.uniform(0.95, 1.05), -1)
            moq = int(rng.choice([10, 20, 50, 100]))
            rows.append({
                "id": vm_id, "vendor_id": v, "material_id": m,
                "unit_price": float(price),
                "bulk_min_qty": moq * 5,
                "bulk_unit_price": float(round(price * (1 - rng.uniform(0.08, 0.15)), -1)),
                "moq": moq,
                "lead_time_days": int(max(1, round(base_lead * t.at[v, "speed_factor"] + rng.normal(0, 0.4)))),
                "in_stock": bool(rng.random() < 0.9),
                "quality_score": float(round(np.clip(t.at[v, "quality_true"] + rng.normal(0, 0.25), 1, 5), 1)),
            })
            vm_id += 1
    return pd.DataFrame(rows)


def make_transactions(vm: pd.DataFrame, truth: pd.DataFrame) -> pd.DataFrame:
    t = truth.set_index("vendor_id")
    today = date(2026, 11, 1)
    rows = []
    for _, r in vm.iterrows():
        rel, q = t.at[r.vendor_id, "reliability_true"], t.at[r.vendor_id, "quality_true"]
        for _ in range(int(rng.poisson(9))):
            late = rng.random() > rel
            delay = int(rng.integers(1, 5)) if late else -int(rng.random() < 0.15)
            promised = int(r.lead_time_days)
            rows.append({
                "vendor_id": int(r.vendor_id), "material_id": int(r.material_id),
                "qty": int(max(r.moq, round(rng.lognormal(np.log(120), 0.7)))),
                "unit_price": float(round(r.unit_price * (1 + rng.normal(0, 0.03)), -1)),
                "ordered_at": (today - timedelta(days=int(rng.integers(1, 548)))).isoformat(),
                "promised_days": promised,
                "actual_days": max(1, promised + delay),
                "defect_rate": float(round(np.clip(rng.normal((5 - q) / 20, 0.015), 0, 0.3), 3)),
            })
    tx = pd.DataFrame(rows)

    # deliberate dirt so preprocessing has real work to do
    n = len(tx)
    tx.loc[rng.choice(n, int(0.02 * n), replace=False), "defect_rate"] = np.nan
    tx.loc[rng.choice(n, int(0.005 * n), replace=False), "actual_days"] = rng.integers(40, 90, int(0.005 * n))
    dupes = tx.loc[rng.choice(n, int(0.01 * n), replace=False)]
    tx = pd.concat([tx, dupes], ignore_index=True)
    tx = tx.sample(frac=1, random_state=SEED).reset_index(drop=True)
    tx.insert(0, "id", range(1, len(tx) + 1))
    return tx


def main() -> None:
    materials = make_materials()
    vendors, truth = make_vendors()
    vm = make_vendor_materials(truth)
    tx = make_transactions(vm, truth)

    materials.to_csv(OUT / "materials.csv", index=False)
    vendors.to_csv(OUT / "vendors.csv", index=False)
    vm.to_csv(OUT / "vendor_materials.csv", index=False)
    tx.to_csv(OUT / "transactions.csv", index=False)
    truth[["vendor_id", "reliability_true", "quality_true"]].to_csv(LATENT / "vendor_truth.csv", index=False)

    per_mat = vm.groupby("material_id").size()
    print(f"materials={len(materials)} vendors={len(vendors)} vendor_materials={len(vm)} transactions={len(tx)}")
    print(f"vendors per material: min={per_mat.min()} max={per_mat.max()}")
    print(f"dirt: missing defect_rate={tx.defect_rate.isna().sum()} outliers(actual_days>30)={(tx.actual_days > 30).sum()}")


if __name__ == "__main__":
    main()
