# Baseline and selected hyperparameters

## random_forest · url_only

Baseline candidate C003. Selected candidate C022. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| n_estimators | 200 | [50, 100, 200, 300, 500] | 300 | CHANGED | C022 (kho nghiên cứu nội bộ) |
| min_samples_leaf | 2 | [1, 2, 4, 8] | 4 | CHANGED | C022 (kho nghiên cứu nội bộ) |
| n_jobs | -1 | [-1] | -1 | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| class_weight | balanced | [None, 'balanced'] | None | CHANGED | C022 (kho nghiên cứu nội bộ) |
| max_depth | None | [10, 20, 30, None] | 10 | CHANGED | C022 (kho nghiên cứu nội bộ) |
| max_features | sqrt | ['sqrt', 'log2', 0.5] | log2 | CHANGED | C022 (kho nghiên cứu nội bộ) |
| min_samples_split | 2 | [2, 5, 10] | 5 | CHANGED | C022 (kho nghiên cứu nội bộ) |
| bootstrap | True | [True] | True | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| ccp_alpha | 0.0 | [0.0] | 0.0 | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| criterion | gini | ['gini'] | gini | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| max_leaf_nodes | None | [None] | None | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| max_samples | None | [None] | None | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| min_impurity_decrease | 0.0 | [0.0] | 0.0 | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| min_weight_fraction_leaf | 0.0 | [0.0] | 0.0 | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| monotonic_cst | None | [None] | None | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| oob_score | False | [False] | False | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| verbose | 0 | [0] | 0 | UNCHANGED | C022 (kho nghiên cứu nội bộ) |
| warm_start | False | [False] | False | UNCHANGED | C022 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.9040304123511386 | 0.9084686466136822 | 0.004438234262543639 |
| precision | 0.8213215859030837 | 0.7715162279993542 | -0.04980535790372953 |
| recall | 0.9273776362912853 | 0.9506565857540787 | 0.023278949462793408 |
| fpr | 0.17780115728563914 | 0.2481150271786779 | 0.07031386989303876 |
| training_seconds | 6.678999001999955 | 7.285433090999959 | 0.606434089000004 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

## random_forest · url_html

Baseline candidate C003. Selected candidate C019. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| n_estimators | 200 | [50, 100, 200, 300, 500] | 300 | CHANGED | C019 (kho nghiên cứu nội bộ) |
| min_samples_leaf | 2 | [1, 2, 4, 8] | 2 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| n_jobs | -1 | [-1] | -1 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| class_weight | balanced | [None, 'balanced'] | None | CHANGED | C019 (kho nghiên cứu nội bộ) |
| max_depth | None | [10, 20, 30, None] | None | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| max_features | sqrt | ['sqrt', 'log2', 0.5] | log2 | CHANGED | C019 (kho nghiên cứu nội bộ) |
| min_samples_split | 2 | [2, 5, 10] | 5 | CHANGED | C019 (kho nghiên cứu nội bộ) |
| bootstrap | True | [True] | True | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| ccp_alpha | 0.0 | [0.0] | 0.0 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| criterion | gini | ['gini'] | gini | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| max_leaf_nodes | None | [None] | None | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| max_samples | None | [None] | None | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| min_impurity_decrease | 0.0 | [0.0] | 0.0 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| min_weight_fraction_leaf | 0.0 | [0.0] | 0.0 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| monotonic_cst | None | [None] | None | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| oob_score | False | [False] | False | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| verbose | 0 | [0] | 0 | UNCHANGED | C019 (kho nghiên cứu nội bộ) |
| warm_start | False | [False] | False | UNCHANGED | C019 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.9562926829268292 | 0.9575381493189712 | 0.0012454663921419584 |
| precision | 0.8877015033508422 | 0.8891103460771879 | 0.0014088427263456715 |
| recall | 0.9751293274970155 | 0.9763231197771588 | 0.0011937922801432688 |
| fpr | 0.10871471155532177 | 0.10731194108364019 | -0.0014027704716815803 |
| training_seconds | 4.730830580999964 | 6.963461011000163 | 2.2326304300001993 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

## xgboost · url_only

Baseline candidate C003. Selected candidate C006. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| n_estimators | 250 | [100, 200, 250, 300, 500] | 100 | CHANGED | C006 (kho nghiên cứu nội bộ) |
| learning_rate | 0.06 | [0.01, 0.03, 0.06, 0.1] | 0.06 | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_depth | 5 | [3, 5, 7, 9] | 3 | CHANGED | C006 (kho nghiên cứu nội bộ) |
| tree_method | hist | ['hist'] | hist | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| eval_metric | logloss | ['logloss'] | logloss | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| n_jobs | 2 | [2] | 2 | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| min_child_weight | 1 | [1, 3, 5] | 1 | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| subsample | 1.0 | [0.7, 0.8, 1.0] | 1.0 | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| colsample_bytree | 1.0 | [0.7, 0.8, 1.0] | 1.0 | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| gamma | 0 | [0, 0.1, 0.5] | 0.5 | CHANGED | C006 (kho nghiên cứu nội bộ) |
| reg_alpha | 0 | [0, 0.1, 1] | 0.1 | CHANGED | C006 (kho nghiên cứu nội bộ) |
| reg_lambda | 1 | [0.1, 1, 5, 10] | 10 | CHANGED | C006 (kho nghiên cứu nội bộ) |
| objective | binary:logistic | ['binary:logistic'] | binary:logistic | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| base_score | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| booster | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| callbacks | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| colsample_bylevel | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| colsample_bynode | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| early_stopping_rounds | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| enable_categorical | False | [False] | False | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| feature_types | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| feature_weights | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| grow_policy | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| importance_type | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| interaction_constraints | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_bin | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_cat_threshold | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_cat_to_onehot | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_delta_step | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| max_leaves | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| missing | NaN | ['NaN'] | NaN | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| monotone_constraints | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| multi_strategy | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| num_parallel_tree | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| sampling_method | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| scale_pos_weight | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| validate_parameters | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |
| verbosity | None | [None] | None | UNCHANGED | C006 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.9006376195536663 | 0.9061064936050705 | 0.005468874051404171 |
| precision | 0.7600896860986547 | 0.7646116893514812 | 0.004522003252826479 |
| recall | 0.9442896935933147 | 0.9500596896140071 | 0.005769996020692392 |
| fpr | 0.26266877082237416 | 0.2577590741714887 | -0.004909696650885476 |
| training_seconds | 2.176421194999989 | 0.1695802989999038 | -2.006840896000085 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

## xgboost · url_html

Baseline candidate C003. Selected candidate C004. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| n_estimators | 250 | [100, 200, 250, 300, 500] | 300 | CHANGED | C004 (kho nghiên cứu nội bộ) |
| learning_rate | 0.06 | [0.01, 0.03, 0.06, 0.1] | 0.06 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_depth | 5 | [3, 5, 7, 9] | 5 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| tree_method | hist | ['hist'] | hist | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| eval_metric | logloss | ['logloss'] | logloss | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| n_jobs | 2 | [2] | 2 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| min_child_weight | 1 | [1, 3, 5] | 1 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| subsample | 1.0 | [0.7, 0.8, 1.0] | 1.0 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| colsample_bytree | 1.0 | [0.7, 0.8, 1.0] | 1.0 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| gamma | 0 | [0, 0.1, 0.5] | 0 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| reg_alpha | 0 | [0, 0.1, 1] | 0 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| reg_lambda | 1 | [0.1, 1, 5, 10] | 1 | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| objective | binary:logistic | ['binary:logistic'] | binary:logistic | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| base_score | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| booster | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| callbacks | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| colsample_bylevel | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| colsample_bynode | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| early_stopping_rounds | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| enable_categorical | False | [False] | False | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| feature_types | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| feature_weights | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| grow_policy | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| importance_type | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| interaction_constraints | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_bin | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_cat_threshold | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_cat_to_onehot | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_delta_step | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| max_leaves | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| missing | NaN | ['NaN'] | NaN | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| monotone_constraints | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| multi_strategy | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| num_parallel_tree | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| sampling_method | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| scale_pos_weight | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| validate_parameters | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |
| verbosity | None | [None] | None | UNCHANGED | C004 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.9507907262398281 | 0.952014468772848 | 0.0012237425330199336 |
| precision | 0.8328850033624747 | 0.8410674825769165 | 0.008182479214441818 |
| recall | 0.9856744926382809 | 0.9844807003581377 | -0.0011937922801431577 |
| fpr | 0.17429423110643522 | 0.16394879887778363 | -0.010345432228651585 |
| training_seconds | 0.8664731949997986 | 1.0314772749999293 | 0.16500408000013067 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

## mlp · url_only

Baseline candidate C002. Selected candidate C021. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| hidden | 64 | [32, 64, 128, 256] | 256 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| batch_size | 128 | [32, 64, 128, 256] | 64 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| epochs | 80 | [80, 150, 200] | 150 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| patience | 8 | [8] | 8 | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| learning_rate | 0.001 | [0.0001, 0.0005, 0.001] | 0.0005 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| weight_decay | 0 | [0, 0.0001, 0.001] | 0.001 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| dropout | 0 | [0, 0.1, 0.3] | 0.1 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| hidden_layers | 1 | [1] | 1 | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| activation | ReLU | ['ReLU'] | ReLU | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| output | one logit | ['one logit'] | one logit | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| loss | BCEWithLogitsLoss | ['BCEWithLogitsLoss'] | BCEWithLogitsLoss | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| optimizer | Adam | ['Adam'] | Adam | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| scaler | StandardScaler | ['StandardScaler'] | StandardScaler | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| scheduler | None | [None] | None | UNCHANGED | C021 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.8998328013375892 | 0.9024251610458507 | 0.002592359708261438 |
| precision | 0.7623953638119768 | 0.7577155583837099 | -0.004679805428266959 |
| recall | 0.942300039793076 | 0.9476721050537207 | 0.0053720652606447095 |
| fpr | 0.25881115202524985 | 0.2670524285463791 | 0.00824127652112927 |
| training_seconds | 18.97628935399996 | 34.450650683999925 | 15.474361329999965 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

## mlp · url_html

Baseline candidate C002. Selected candidate C021. Search search-v2.0. CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`.

| Hyperparameter | Baseline V1 | Search Space | Selected V2 | Changed? | Experimental Evidence |
|---|---|---|---|---|---|
| hidden | 64 | [32, 64, 128, 256] | 256 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| batch_size | 128 | [32, 64, 128, 256] | 64 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| epochs | 80 | [80, 150, 200] | 150 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| patience | 8 | [8] | 8 | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| learning_rate | 0.001 | [0.0001, 0.0005, 0.001] | 0.0005 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| weight_decay | 0 | [0, 0.0001, 0.001] | 0.001 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| dropout | 0 | [0, 0.1, 0.3] | 0.1 | CHANGED | C021 (kho nghiên cứu nội bộ) |
| hidden_layers | 1 | [1] | 1 | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| activation | ReLU | ['ReLU'] | ReLU | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| output | one logit | ['one logit'] | one logit | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| loss | BCEWithLogitsLoss | ['BCEWithLogitsLoss'] | BCEWithLogitsLoss | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| optimizer | Adam | ['Adam'] | Adam | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| scaler | StandardScaler | ['StandardScaler'] | StandardScaler | UNCHANGED | C021 (kho nghiên cứu nội bộ) |
| scheduler | None | [None] | None | UNCHANGED | C021 (kho nghiên cứu nội bộ) |

| Measure | Baseline OOF | Selected OOF | Selected − baseline |
|---|---|---|---|
| f2 | 0.9300406784864533 | 0.934711311112806 | 0.0046706326263527 |
| precision | 0.8140745717164931 | 0.8012422360248447 | -0.012832335691648433 |
| recall | 0.9643851969757262 | 0.9753282928770394 | 0.010943095901313149 |
| fpr | 0.1941083640189374 | 0.21322111169559882 | 0.019112747676661407 |
| training_seconds | 21.570201995999696 | 35.1994047390001 | 13.629202743000405 |

Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. Best configuration found within the predefined search space and search budget.

