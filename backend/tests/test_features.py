import numpy as np
import pandas as pd

from app.core.features import FEATURE_NAMES, build_candidate_features, clean_transactions


def _tx(rows):
    cols = ["id", "vendor_id", "material_id", "qty", "unit_price", "ordered_at",
            "promised_days", "actual_days", "defect_rate"]
    return pd.DataFrame(rows, columns=cols)


def _vm():
    return pd.DataFrame([
        {"id": 1, "vendor_id": 1, "material_id": 1, "unit_price": 1000.0, "bulk_min_qty": 100,
         "bulk_unit_price": 900.0, "moq": 20, "lead_time_days": 2, "in_stock": True, "quality_score": 4.5},
        {"id": 2, "vendor_id": 2, "material_id": 1, "unit_price": 800.0, "bulk_min_qty": 500,
         "bulk_unit_price": 700.0, "moq": 50, "lead_time_days": 5, "in_stock": False, "quality_score": 3.5},
        {"id": 3, "vendor_id": 3, "material_id": 2, "unit_price": 5000.0, "bulk_min_qty": 100,
         "bulk_unit_price": 4500.0, "moq": 10, "lead_time_days": 3, "in_stock": True, "quality_score": 4.0},
    ])


def test_clean_removes_duplicates_outliers_and_missing():
    tx = _tx([
        [1, 1, 1, 100, 1000, "2026-01-01", 2, 2, 0.02],
        [2, 1, 1, 100, 1000, "2026-01-01", 2, 2, 0.02],   # duplicate of row 1 (different id)
        [3, 1, 1, 50, 1000, "2026-02-01", 2, 60, 0.01],   # impossible delivery time
        [4, 1, 1, 80, 1000, "2026-03-01", 2, 3, np.nan],  # missing defect rate
    ])
    clean = clean_transactions(tx)
    assert len(clean) == 2
    assert clean["actual_days"].max() <= 30
    assert clean["defect_rate"].isna().sum() == 0


def test_bulk_price_only_at_or_above_threshold():
    vm, tx = _vm(), clean_transactions(_tx([]))
    below = build_candidate_features({"material_id": 1, "qty": 99, "deadline_days": 3,
                                      "w_price": .3, "w_speed": .5, "w_quality": .2}, vm, tx)
    at = build_candidate_features({"material_id": 1, "qty": 100, "deadline_days": 3,
                                   "w_price": .3, "w_speed": .5, "w_quality": .2}, vm, tx)
    assert below.loc[1, "unit_price_eff"] == 1000.0
    assert at.loc[1, "unit_price_eff"] == 900.0


def test_feature_columns_order_and_no_nan():
    vm = _vm()
    tx = clean_transactions(_tx([[1, 1, 1, 100, 1000, "2026-01-01", 2, 3, 0.02]]))
    f = build_candidate_features({"material_id": 1, "qty": 100, "deadline_days": 3,
                                  "w_price": .3, "w_speed": .5, "w_quality": .2}, vm, tx)
    assert list(f.columns) == FEATURE_NAMES
    assert sorted(f.index) == [1, 2]
    assert not f.isna().any().any()
    assert f.loc[2, "slack_typ"] == -2   # 3-day deadline, 5-day lead time
