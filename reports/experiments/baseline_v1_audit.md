# Baseline V1 audit

18/18 distinct slots, attempts and paths. All checkpoint, config and metric hashes match. Validation replay used each checkpoint, the locked feature order and all 19 thresholds. Classification metrics and threshold match (absolute tolerance 1e-12). Rank metrics use a 1e-5 absolute cross-platform tolerance after observing small cross-platform MLP and parallel RF ranking differences; signed per-run differences are recorded in effective_parameters.json. Historical hardware checks READY.

| Model | Modality | Seed | Device | F2 | Threshold | Best epoch |
|---|---|---:|---|---:|---:|---:|
| random_forest | url_only | 42 | cpu | 0.89635854 | 0.1 | — |
| random_forest | url_only | 43 | cpu | 0.89889640 | 0.15 | — |
| random_forest | url_only | 44 | cpu | 0.89889640 | 0.15 | — |
| xgboost | url_only | 42 | cpu | 0.89759573 | 0.1 | — |
| xgboost | url_only | 43 | cpu | 0.89759573 | 0.1 | — |
| xgboost | url_only | 44 | cpu | 0.89759573 | 0.1 | — |
| mlp | url_only | 42 | cuda | 0.87441526 | 0.15 | 30 |
| mlp | url_only | 43 | cuda | 0.87620579 | 0.15 | 20 |
| mlp | url_only | 44 | cuda | 0.88261810 | 0.15 | 42 |
| random_forest | url_html | 42 | cpu | 0.95648981 | 0.25 | — |
| random_forest | url_html | 43 | cpu | 0.95901639 | 0.2 | — |
| random_forest | url_html | 44 | cpu | 0.95880423 | 0.2 | — |
| xgboost | url_html | 42 | cpu | 0.96048299 | 0.1 | — |
| xgboost | url_html | 43 | cpu | 0.96048299 | 0.1 | — |
| xgboost | url_html | 44 | cpu | 0.96048299 | 0.1 | — |
| mlp | url_html | 42 | cuda | 0.94677770 | 0.15 | 30 |
| mlp | url_html | 43 | cuda | 0.94004709 | 0.15 | 21 |
| mlp | url_html | 44 | cuda | 0.94438425 | 0.15 | 34 |

Maximum absolute MLP replay differences: average_precision 1.23321806e-06, pr_auc 8.94926919e-07, roc_auc 1.51964829e-06.

XGBoost url_only: 1 distinct tree dumps, 1 distinct Validation probability arrays across three distinct attempts. Estimator random_state matches each seed. Full row/column sampling and CPU hist are consistent with these results.

XGBoost url_html: 1 distinct tree dumps, 1 distinct Validation probability arrays across three distinct attempts. Estimator random_state matches each seed. Full row/column sampling and CPU hist are consistent with these results.

Per-run estimator parameters, native booster settings, versions, hardware and MLP epochs: results/baseline_v1/effective_parameters.json. Manifest and history fingerprints: manifests/baseline_v1.json.
