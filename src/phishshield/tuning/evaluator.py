import time

import joblib
import numpy as np
from sklearn.metrics import log_loss

from phishshield.evaluation.metrics import choose, scores
from phishshield.features.pipeline import schema
from phishshield.models.mlp import fit
from phishshield.utils.hardware import booster_device

from .design import folds


def tree(model, hp, seed, device):
    if model == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(random_state=seed, **hp)
    from xgboost import XGBClassifier

    return XGBClassifier(random_state=seed, device=device, **hp)


def evaluate(frame, mode, model, hp, plan, device, stage):
    cols = schema(mode)
    x = frame[cols].to_numpy()
    y = frame.label.to_numpy()
    oof = np.full(len(frame), np.nan)
    history, costs = {}, []
    seed = plan["training_seed"]
    for fold in range(plan["folds"]):
        train = np.flatnonzero(frame.fold != fold)
        valid = np.flatnonzero(frame.fold == fold)
        started = time.perf_counter()
        path = stage / f"fold_{fold}.joblib"
        if model == "mlp":
            inner = folds(frame.iloc[train], 3, plan["cv_seed"])
            learn = train[inner.fold.to_numpy() != 0]
            stop = train[inner.fold.to_numpy() == 0]

            def checkpoint(est, trace):
                joblib.dump(
                    dict(estimator=est, columns=cols, architecture=hp), path, compress=3
                )

            trace = fit(
                x[learn], y[learn], x[stop], y[stop], seed, hp, checkpoint, device
            )
            history[str(fold)] = dict(
                epochs=trace,
                best_epoch=min(trace, key=lambda e: e["val_loss"])["epoch"],
                fit_rows=len(learn),
                stopping_rows=len(stop),
                refits=0,
            )
        else:
            estimator = tree(model, hp, seed, device).fit(x[train], y[train])
            if model == "xgboost":
                booster_device(estimator, device)
            joblib.dump(dict(estimator=estimator, columns=cols), path, compress=3)
        seconds = time.perf_counter() - started
        estimator = joblib.load(path)["estimator"]
        started = time.perf_counter()
        oof[valid] = estimator.predict_proba(x[valid])[:, 1]
        costs.append(
            dict(
                fold=fold,
                rows=len(valid),
                training_seconds=seconds,
                inference_seconds=time.perf_counter() - started,
                model_bytes=path.stat().st_size,
            )
        )
    if not np.isfinite(oof).all() or ((oof < 0) | (oof > 1)).any():
        raise ValueError("Invalid or incomplete OOF predictions")
    threshold, metrics = choose(y, oof, plan["thresholds"])
    metrics.update(
        threshold=threshold,
        log_loss=float(log_loss(y, oof)),
        training_seconds=sum(f["training_seconds"] for f in costs),
        inference_seconds=sum(f["inference_seconds"] for f in costs),
        model_bytes=float(np.mean([f["model_bytes"] for f in costs])),
    )
    for row in costs:
        idx = frame.fold == row["fold"]
        row["metrics_at_pooled_threshold"] = scores(y[idx], oof[idx], threshold)
    pred = frame[["serial_number", "fold", "label"]].assign(probability=oof)
    pred.to_parquet(stage / "oof_predictions.parquet", index=False)
    return metrics, costs, history
