# Baseline V1 vs Tuned V2 · Validation

| Model | Modality | Baseline F2 (%) | Tuned F2 (%) | Δ F2 (pp) | Baseline FPR (%) | Tuned FPR (%) | Δ FPR (pp) |
|---|---|---|---|---|---|---|---|
| mlp | url_html | 94.374 | 94.850 | 0.476 | 14.430 | 14.839 | 0.409 |
| mlp | url_only | 87.775 | 87.657 | -0.118 | 23.077 | 24.714 | 1.637 |
| random_forest | url_html | 95.810 | 95.920 | 0.110 | 9.602 | 10.011 | 0.409 |
| random_forest | url_only | 89.805 | 89.707 | -0.098 | 26.732 | 22.368 | -4.364 |
| xgboost | url_html | 96.048 | 95.900 | -0.148 | 8.838 | 8.838 | 0.000 |
| xgboost | url_only | 89.760 | 88.736 | -1.023 | 24.468 | 34.697 | 10.229 |

Three matched seeds per complete pair. paired_seeds.csv and paired_summary.csv include sample SD (ddof=1), extrema, paired mean differences and relative percentages. Missing timing = NOT_AVAILABLE. Training time includes checkpoint publication in final runs. Latency averages a single batch on the recorded host. Compare costs only within matching hardware/measurement conditions.

A negative mean F2 difference requires Project Leader review before Test. Three seeds support descriptive comparisons only. Baseline ablation holds hyperparameters fixed. Tuned modalities may select different configurations.

Project Leader review required for lower mean Validation F2.

| Model | Modality | Δ F2 (pp) |
|---|---|---|
| mlp | url_only | -0.11809807340007472 |
| random_forest | url_only | -0.09821555121948637 |
| xgboost | url_html | -0.1478593343437029 |
| xgboost | url_only | -1.0232610838063594 |
