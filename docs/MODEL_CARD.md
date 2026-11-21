# Model card — Firaza vendor ranker

## Purpose
Given a procurement need (material, quantity, deadline, and how much the user cares about price, speed, and quality), order the candidate vendors from most to least suitable. **Decision support only:** the owner or staff makes the final choice.

## Algorithm
- **LightGBM `LGBMRanker`**, objective `lambdarank` (LambdaMART: gradient-boosted decision trees trained to optimize NDCG; Burges 2010, Ke et al. 2017).
- Each procurement request is one *query group*; its candidate vendors are the items to order.
- Hyperparameters: 500 trees max, learning rate 0.05, 15 leaves, min 20 samples per leaf, 80% row and column subsampling, early stopping after 30 rounds without validation improvement. The best model has **63 trees**.
- Trained by us from scratch on our own data. No pretrained model, no AutoML.

## Data
Synthetic data described in `docs/DATA_CARD.md`: 3,000 simulated requests, 44,253 (request, vendor) rows, 17 features, graded labels 0–4. Split **by request** (70% train / 15% validation / 15% test), so no request appears in two splits.

## Results (test split, 450 requests the model never saw)

| Method | NDCG@1 | NDCG@3 | NDCG@5 | Kendall τ |
|---|---|---|---|---|
| **LightGBM LambdaRank (ours)** | **0.959** | **0.933** | **0.941** | **0.743** |
| Baseline: cheapest first | 0.723 | 0.733 | 0.756 | 0.425 |
| Baseline: weighted sum (user weights × normalized price/speed/quality) | 0.813 | 0.788 | 0.810 | 0.524 |
| Baseline: TOPSIS | 0.734 | 0.718 | 0.748 | 0.438 |
| Control: same model trained on shuffled labels | 0.437 | 0.456 | 0.498 | −0.013 |
| Ablation: without the two deadline-slack features | 0.963 | 0.939 | 0.940 | 0.744 |

How to read this:
- **NDCG@3 = 0.933**: the vendors that truly fit best land in the top 3 almost all the time. This meets the Project Plan target (≥ 0.85).
- The model beats the strongest simple method (a weighted-sum "spreadsheet formula", 0.788) by 0.145. The extra comes from things a linear formula cannot express: hard deadline misses, MOQ problems, stock-outs, and "urgent orders need reliable vendors".
- The **shuffled-label control** collapses to chance level (Kendall τ ≈ 0), which shows the score comes from real patterns and not from a bug in the evaluation.
- The **ablation** shows the slack features are redundant: `slack = deadline − lead time`, and the trees can rebuild that from `deadline_days` and `lead_typ`.

Most important features (total gain): price relative to other candidates, the user's price priority, MOQ ratio, deadline slack, defect rate, stock, lead time, quality score. Chart: `ml/reports/feature_importance.png`.

## Explainability
For every recommendation the app computes LightGBM's per-feature contributions (`pred_contrib=True`), which add up exactly to the score. They are shown as a chart and passed to the RAG explanation, so the generated text reflects what the model actually used.

## Limitations
- **Synthetic labels.** Labels come from a utility function we wrote (with hidden truth and noise). The results show the pipeline works and learns sensible trade-offs; they are not a measurement on Firaza's real decisions.
- No feedback loop yet: the owner's actual choices are not used to retrain.
- Prices, lead times, and reliability are assumed stable over the history window.
- Edge case found in live testing: when **no** vendor can meet the deadline (e.g. premium hamper boxes within 1 day; the fastest takes 3), the order leans on price, and a vendor with a low on-time rate (55%) was ranked first. The app flags every vendor as missing the deadline so the user sees the risk. A fix would add training requests where no candidate meets the deadline, with labels that favor reliability in that case.

## Intended use
Shortlisting and comparing vendors for a single material order at Firaza. Not for automatic purchasing.

## How to retrain
```bash
.venv/Scripts/python ml/generate_data.py          # or replace ml/data/*.csv with real exports
.venv/Scripts/python ml/build_ranking_dataset.py
.venv/Scripts/python ml/train_ranker.py           # writes backend/artifacts/ranker.txt
.venv/Scripts/python ml/evaluate.py               # writes ml/reports/metrics.*
```
