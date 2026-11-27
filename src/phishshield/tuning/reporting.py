import os
from pathlib import Path
from tempfile import TemporaryDirectory

# Colab's inline backend may be unavailable in the workflow subprocess.
os.environ["MPLBACKEND"] = "Agg"
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phishshield.data.prepare import FEATURES, read_json
from phishshield.training.runs import MEMBERS, config, verified_run
from phishshield.utils.storage import publish, save_json, sha256

from .audit import baseline_runs
from .design import DEVICE, design, protocol, verify_cv
from .search import locked, search_folder

KEYS = ["model", "modality", "seed"]
MEASURES = [
    "f2",
    "fpr",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "macro_f1",
    "roc_auc",
    "pr_auc",
    "average_precision",
    "fnr",
    "training_seconds",
    "inference_ms_per_row",
    "model_bytes",
]


def markdown(headers, rows):
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
        *["| " + " | ".join(map(str, row)) + " |" for row in rows],
    ]


def chart(folder, name, draw):
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    try:
        draw(ax)
        ax.grid(axis="y", alpha=0.2)
        file = folder / (name + ".png")
        fig.savefig(file, dpi=130)
        return file
    finally:
        plt.close(fig)


def trial_summary(folder, rows, spec, selected):
    frame = pd.DataFrame(rows)
    files = []

    def csv(df, name):
        path = folder / name
        df.to_csv(path, index=False)
        files.append(path)

    csv(frame, "tuning_summary.csv")
    axis = spec["search_space"]["sensitivity"]
    count = len(spec["search_space"]["space"][axis])
    sweep = frame.iloc[:count].sort_values(axis)
    csv(sweep, "sensitivity.csv")
    model = spec["model"]

    def plot(df, x, y, name, line=False):
        def draw(ax):
            if line:
                ax.plot(df[x], df[y], "o-")
            else:
                ax.scatter(df[x], df[y])
            ax.set(xlabel=x, ylabel=y, title=f"{model} · {spec['modality']}")

        files.append(chart(folder, name, draw))

    targets = {
        "random_forest": ["f2", "recall", "fpr", "training_seconds", "model_bytes"],
        "xgboost": ["f2", "log_loss", "fpr"],
        "mlp": ["f2"],
    }[model]
    for y in targets:
        plot(sweep, axis, y, axis + "_vs_" + y, True)
    for x, y in {
        "random_forest": [],
        "xgboost": [
            ("learning_rate", "n_estimators"),
            ("max_depth", "f2"),
            ("training_seconds", "f2"),
        ],
        "mlp": [("learning_rate", "f2"), ("batch_size", "f2"), ("model_bytes", "f2")],
    }[model]:
        plot(frame, x, y, x + "_vs_" + y)
    if model == "mlp":
        histories = read_json(folder / selected / "training_history.json")
        for key in ("loss", "val_loss"):

            def draw(ax):
                for fold, item in histories.items():
                    trace = pd.DataFrame(item["epochs"])
                    ax.plot(
                        trace.epoch,
                        trace[key],
                        label=f"fold {fold}, best {item['best_epoch']}",
                    )
                ax.set(
                    xlabel="Epoch", ylabel=key, title=f"{selected} · {spec['modality']}"
                )
                ax.legend()

            files.append(chart(folder, "epoch_vs_" + key, draw))
    diagnostics = [
        "",
        f"Controlled sweep of {axis}. The F2 range was {sweep.f2.min():.6f}–{sweep.f2.max():.6f}; "
        f"training cost ranged from {sweep.training_seconds.min():.3f} to {sweep.training_seconds.max():.3f} seconds. "
        "The sweep table and curves show all controlled settings, including baseline. Multivariable trials can change several parameters at once.",
    ]
    if model == "mlp":
        diagnostics += [
            "",
            "Selected MLP stopping diagnostics (inner subset only).",
            *markdown(
                [
                    "Fold",
                    "Best epoch",
                    "Epochs run",
                    "Train loss at best",
                    "Inner loss at best",
                    "Last train loss",
                    "Last inner loss",
                ],
                [
                    (
                        fold,
                        item["best_epoch"],
                        len(item["epochs"]),
                        item["epochs"][item["best_epoch"] - 1]["loss"],
                        item["epochs"][item["best_epoch"] - 1]["val_loss"],
                        item["epochs"][-1]["loss"],
                        item["epochs"][-1]["val_loss"],
                    )
                    for fold, item in histories.items()
                ],
            ),
            "Inspect widening train/inner loss gaps for overfitting and persistently high losses on both sets for underfitting. Compare against the controlled width sweep.",
        ]
    md = folder / "tuning_summary.md"
    md.write_text(
        "\n".join(
            [
                f"# {model} · {spec['modality']}",
                "",
                f"Selected {selected} by the locked ranking. CV SHA-256 {spec['cv_hash']}.",
                "",
                *markdown(
                    [
                        "Trial",
                        "OOF F2",
                        "Precision",
                        "Recall",
                        "FPR",
                        "Seconds",
                        "Mean bytes",
                    ],
                    frame[
                        [
                            "trial_id",
                            "f2",
                            "precision",
                            "recall",
                            "fpr",
                            "training_seconds",
                            "model_bytes",
                        ]
                    ].values.tolist(),
                ),
                *diagnostics,
            ]
        )
        + "\n",
        "utf8",
    )
    return [*files, md]


def tuned_run(root, model, mode, seed, selection):
    folder = root / "results/tuned_v2" / model / mode / f"seed_{seed}"
    meta = verified_run(root, folder)
    cfg = read_json(folder / "config.json")
    lockfile = search_folder(root, model, mode) / "tuning_lock.json"
    hp = selection["selected_hyperparameters"]
    binding = dict(
        phase="TUNED_V2",
        seed=seed,
        modality=mode,
        device=DEVICE[model],
        selected_trial=selection["selected_trial"],
        tuning_lock_sha256=sha256(lockfile),
    )
    if (
        any(meta.get(k) != v or cfg.get(k) != v for k, v in binding.items())
        or meta["hyperparameters"] != hp
        or cfg["settings"] != hp
        or meta["model"] != model
        or meta["dataset_version"] != 4
        or meta["feature_version"] != selection["definition"]["feature_schema"]
        or meta["split_hash"] != selection["definition"]["protocol"]["split_hash"]
        or meta["threshold"] not in selection["definition"]["protocol"]["thresholds"]
        or meta["hardware"]["hardware_check_status"] != "READY"
        or meta["hardware"]["actual_device"] != DEVICE[model]
        or Path(meta["checkpoint"]).parts[:4]
        != ("checkpoints", "tuned_v2", model, mode)
    ):
        raise ValueError(f"Invalid tuned run {folder}")
    return meta


def hp_table(root, model, mode, lock, cv):
    plan = protocol(root)
    base, candidates = design(root, model)
    bid = next(k for k, hp in candidates.items() if hp == base)
    space = config(root, "tuning/" + model)["space"]
    folder = search_folder(root, model, mode)
    selected = lock["selected_trial"] if lock else None
    # Include fixed model controls alongside sampled controls; seeds and hardware have separate evidence.
    params_file = root / "results/baseline_v1/effective_parameters.json"
    baseline = read_json(params_file)[f"{model}/{mode}/42"]
    fixed = {
        k: v
        for k, v in baseline.get("estimator", {}).items()
        if k not in ("random_state", "device") and k not in base
    }
    if model == "mlp":
        fixed.update(
            hidden_layers=1,
            activation="ReLU",
            output="one logit",
            loss="BCEWithLogitsLoss",
            optimizer="Adam",
            scaler="StandardScaler",
            scheduler=None,
        )
    base = {**base, **fixed}
    current = {**candidates[selected], **fixed} if lock else {}
    lines = [
        f"## {model} · {mode}",
        "",
        f"Baseline candidate {bid}. Selected candidate {selected or 'PENDING'}. Search {plan['version']}. CV SHA-256 `{cv['sha256']}`.",
        "",
    ]
    path = folder.relative_to(root).as_posix()
    evidence = (
        f"[{selected}](../../{path}/{selected}/trial_metrics.json)"
        if lock
        else "PENDING"
    )
    lines += markdown(
        [
            "Hyperparameter",
            "Baseline V1",
            "Search Space",
            "Selected V2",
            "Changed?",
            "Experimental Evidence",
        ],
        [
            (
                k,
                str(v),
                str(space.get(k, [v])),
                str(current[k]) if lock else "PENDING",
                ("UNCHANGED" if current[k] == v else "CHANGED") if lock else "PENDING",
                evidence,
            )
            for k, v in base.items()
        ],
    )
    lines += [
        "",
        *markdown(
            ["Measure", "Baseline OOF", "Selected OOF", "Selected − baseline"],
            metric_differences(folder, bid, selected),
        ),
        "",
        "Selection order: F2, precision, lower FPR, baseline preference, then candidate ID. "
        "Best configuration found within the predefined search space and search budget."
        if lock
        else "Selection evidence and cost differences are PENDING.",
        "",
    ]
    return lines


def metric_differences(folder, baseline, selected):
    pair = (
        [read_json(folder / i / "trial_metrics.json") for i in (baseline, selected)]
        if selected
        else []
    )
    return [
        (k, pair[0][k], pair[1][k], pair[1][k] - pair[0][k])
        if pair
        else (k, "PENDING", "PENDING", "PENDING")
        for k in ("f2", "precision", "recall", "fpr", "training_seconds")
    ]


def performance(root, bases, tuned, out):
    def frame(runs):
        rows = []
        for run in runs:
            values = {k: run[k] for k in KEYS}
            values.update(
                {k: run["metrics"].get(k, run.get(k, np.nan)) for k in MEASURES}
            )
            values["model_bytes"] = (root / run["checkpoint"]).stat().st_size
            rows.append(values)
        return pd.DataFrame(rows, columns=KEYS + MEASURES)

    before, after = frame(bases), frame(tuned)
    paired = before.merge(
        after,
        on=KEYS,
        how="left",
        suffixes=("_baseline", "_tuned"),
        validate="one_to_one",
    )
    for k in MEASURES:
        paired[k + "_delta"] = paired[k + "_tuned"] - paired[k + "_baseline"]
    export = paired.astype(object)
    pending = paired["f2_tuned"].isna()
    export.loc[pending, [k for k in export if k.endswith(("_tuned", "_delta"))]] = (
        "PENDING"
    )
    export.to_csv(out / "paired_seeds.csv", index=False, na_rep="NOT_AVAILABLE")
    full = []
    main = []
    for (model, mode), group in paired.groupby(KEYS[:2]):
        vals = {}
        for k in MEASURES:
            for phase in ("baseline", "tuned", "delta"):
                v = group[k + "_" + phase].dropna()
                stats = v.agg(["mean", "std", "min", "max"]) if len(v) == 3 else {}
                for label in ("mean", "std", "min", "max"):
                    vals[k + "_" + phase + "_" + label] = stats.get(label, np.nan)
            base_mean = vals[k + "_baseline_mean"]
            vals[k + "_relative_percent"] = (
                100 * vals[k + "_delta_mean"] / base_mean if base_mean else np.nan
            )
            if k not in ("training_seconds", "model_bytes", "inference_ms_per_row"):
                vals[k + "_delta_pp"] = 100 * vals[k + "_delta_mean"]
        full.append(dict(model=model, modality=mode, **vals))

        def pct(k):
            v = vals[k + "_mean"]
            return f"{v * 100:.3f}" if pd.notna(v) else "PENDING"

        main.append(
            [
                model,
                mode,
                *[
                    pct(k + "_" + p)
                    for k in ("f2", "fpr")
                    for p in ("baseline", "tuned", "delta")
                ],
            ]
        )
    summary = pd.DataFrame(full)
    export = summary.astype(object)
    dependent = [
        k
        for k in export
        if "_tuned_" in k or "_delta_" in k or k.endswith("_relative_percent")
    ]
    export.loc[summary.f2_tuned_mean.isna(), dependent] = "PENDING"
    export.to_csv(out / "paired_summary.csv", index=False, na_rep="NOT_AVAILABLE")
    lines = [
        "# Baseline V1 vs Tuned V2 · Validation",
        "",
        *markdown(
            [
                "Model",
                "Modality",
                "Baseline F2 (%)",
                "Tuned F2 (%)",
                "Δ F2 (pp)",
                "Baseline FPR (%)",
                "Tuned FPR (%)",
                "Δ FPR (pp)",
            ],
            main,
        ),
        "",
        "Three matched seeds per complete pair. paired_seeds.csv and paired_summary.csv include sample SD (ddof=1), extrema, paired mean differences and relative percentages. Missing timing = NOT_AVAILABLE. Training time includes checkpoint publication in final runs. Latency averages a single batch on the recorded host. Compare costs only within matching hardware/measurement conditions.",
        "",
        "A negative mean F2 difference requires Project Leader review before Test. Three seeds support descriptive comparisons only. Baseline ablation holds hyperparameters fixed. Tuned modalities may select different configurations.",
    ]
    declines = summary.loc[
        summary.f2_delta_mean.lt(0), ["model", "modality", "f2_delta_pp"]
    ]
    if not declines.empty:
        lines += [
            "",
            "Project Leader review required for lower mean Validation F2.",
            "",
            *markdown(["Model", "Modality", "Δ F2 (pp)"], declines.values.tolist()),
        ]
    if len(tuned) == 18:
        labels = summary.model + "\n" + summary.modality
        for measure in ("f2", "recall", "precision", "fpr"):

            def draw(ax):
                for phase, offset in (("baseline", -0.19), ("tuned", 0.19)):
                    ax.bar(
                        np.arange(len(summary)) + offset,
                        summary[f"{measure}_{phase}_mean"],
                        width=0.38,
                        yerr=summary[f"{measure}_{phase}_std"],
                        label=phase,
                    )
                ax.set_xticks(np.arange(len(summary)), labels, fontsize=7)
                ax.set_ylabel(measure + " · mean ± sample SD")
                ax.legend()

            chart(out, measure + "_by_phase", draw)

        def modalities(ax):
            for mode, items in summary.groupby("modality"):
                ax.plot(items.model, items.f2_tuned_mean, "o-", label=mode)
            ax.legend()
            ax.set_ylabel("Tuned Validation F2")

        chart(out, "modalities", modalities)
        for cost in ("model_bytes", "training_seconds"):

            def draw(ax):
                for (m, mode), g in paired.groupby(KEYS[:2]):
                    for phase, marker in (("baseline", "x"), ("tuned", "o")):
                        available = g[cost + "_" + phase].notna()
                        if available.any():
                            ax.scatter(
                                g.loc[available, cost + "_" + phase],
                                g.loc[available, "f2_" + phase],
                                marker=marker,
                                label=f"{m}/{mode} {phase} ({DEVICE[m]})",
                            )
                ax.set(xlabel=cost, ylabel="Validation F2")
                ax.legend(fontsize=7)

            chart(out, cost + "_vs_f2", draw)
    return lines


def reports(root):
    from .design import exclusive

    with exclusive(root / "results/comparisons/v2"):
        return write_reports(root)


def write_reports(root):
    out = root / "results/comparisons/v2"
    cv = verify_cv(root)
    bases = list(baseline_runs(root))
    tuned, registry, decisions = [], [], []
    lines = ["# Baseline and selected hyperparameters", ""]
    for model in MEMBERS:
        for mode in FEATURES:
            folder = search_folder(root, model, mode)
            lock = (
                locked(root, model, mode)
                if (folder / "tuning_lock.json").exists()
                else None
            )
            if lock:
                decisions.append(
                    (
                        model,
                        mode,
                        lock["selected_trial"],
                        str(lock["selected_hyperparameters"]),
                    )
                )
            lines += hp_table(root, model, mode, lock, cv)
            for seed in (42, 43, 44):
                p = (
                    root
                    / "results/tuned_v2"
                    / model
                    / mode
                    / f"seed_{seed}"
                    / "run_manifest.json"
                )
                if p.exists() and read_json(p)["status"] == "COMPLETED":
                    if not lock:
                        raise ValueError("Tuned run requires a lock")
                    tuned.append(tuned_run(root, model, mode, seed, lock))
                    registry.append(
                        dict(
                            model=model,
                            modality=mode,
                            seed=seed,
                            path=p.relative_to(root).as_posix(),
                            sha256=sha256(p),
                        )
                    )
    save_json(root / "manifests/tuned_v2.json", dict(phase="TUNED_V2", runs=registry))
    docs = root / "reports/experiments"
    (docs / "hyperparameter_comparison.md").write_text("\n".join(lines) + "\n", "utf8")
    (docs / "baseline_vs_tuned_report.md").write_text(
        "\n".join(performance(root, bases, tuned, out)) + "\n", "utf8"
    )
    if len(decisions) == len(MEMBERS) * len(FEATURES):
        path = root / "docs/EXPERIMENT_PROTOCOL.md"
        marker = "<!-- selected-hyperparameters-v2 -->"
        current = path.read_text("utf8").split(marker)[0].rstrip()
        appendix = [
            marker,
            "## Cấu hình đã khóa theo kết quả OOF",
            "",
            *markdown(
                ["Model", "Modality", "Selected trial", "Selected hyperparameters"],
                decisions,
            ),
        ]
        with TemporaryDirectory() as tmp:
            stage = Path(tmp) / path.name
            stage.write_text(current + "\n\n" + "\n".join(appendix) + "\n", "utf8")
            publish(stage, path)
    return dict(baseline=len(bases), tuned=len(tuned))
