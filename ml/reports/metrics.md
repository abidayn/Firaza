# Ranking evaluation (test split, 450 requests)

| Method | NDCG@1 | NDCG@3 | NDCG@5 | Kendall τ |
|---|---|---|---|---|
| lightgbm_lambdarank | 0.9591 | 0.933 | 0.9405 | 0.7433 |
| baseline_cheapest | 0.7228 | 0.7326 | 0.7561 | 0.4245 |
| baseline_weighted_sum | 0.8127 | 0.7882 | 0.8104 | 0.5238 |
| baseline_topsis | 0.7335 | 0.7179 | 0.7479 | 0.4382 |
| control_shuffled_labels | 0.4373 | 0.4561 | 0.4977 | -0.0133 |
| ablation_no_slack_features | 0.9633 | 0.9386 | 0.9398 | 0.7444 |

## Conclusion

The trained LambdaRank model reaches NDCG@3 = 0.933 on unseen requests, which meets the 0.85 target from the Project Plan. It beats every baseline; the strongest baseline is `baseline_weighted_sum` at NDCG@3 = 0.7882.

The shuffled-label control scores NDCG@3 = 0.4561, so the model's score comes from real patterns in the features, not from chance or from the evaluation code.

Removing the deadline-slack features changes NDCG@3 only to 0.9386 (+0.0056). They are redundant: slack = deadline - lead time, and the model still sees deadline_days and lead_typ, so the trees rebuild that comparison themselves. The deadline information matters; this particular encoding of it does not.

Limitation: labels come from a simulated utility function (see docs/DATA_CARD.md). These numbers show the pipeline works on simulated data; they are not a measurement of accuracy on Firaza's real data.