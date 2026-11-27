import os

# The batch interpreter does not contain the Colab kernel's inline backend.
os.environ["MPLBACKEND"] = "Agg"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from phishshield.data.prepare import FEATURES, INDEX, prepare
from phishshield.data.splits import SPLIT, lock_split
from phishshield.utils.storage import publish, save_json, sha256, verify_saved_artifact
from phishshield.data.prepare import read_json

EDA_OUTPUTS = (
    "reports/eda/eda_report.md",
    "results/figures/train_distributions.png",
    "results/figures/train_correlations.png",
)


def eda_inputs(cache, lock):
    return {
        "split": lock["sha256"],
        "cohort": lock["cohort_sha256"],
        "features": cache["artifacts"][FEATURES["url_html"]],
        "eda_revision": 1,
    }


def eda(root, runtime):
    cache = prepare(root, runtime)
    lock = lock_split(root, runtime)
    receipt = root / "manifests/eda.json"
    inputs = eda_inputs(cache, lock)
    if receipt.is_file():
        saved = read_json(receipt)
        if saved["inputs"] == inputs:
            for rel in EDA_OUTPUTS:
                verify_saved_artifact(root / rel, saved["outputs"][rel])
            return root / EDA_OUTPUTS[0]
    ids = pd.read_csv(root / SPLIT).query("split == 'train'")
    df = ids.merge(pd.read_csv(root / INDEX)).merge(
        pd.read_csv(root / FEATURES["url_html"])
    )
    cols = cache["schemas"]["url_html"] + ["html_bytes"]
    path = runtime / "results/figures"
    path.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 3, figsize=(13, 10))
    df.label.value_counts().sort_index().plot.bar(
        ax=axes.flat[0], title="Train • số mẫu theo nhãn"
    )
    for ax, col in zip(
        list(axes.flat)[1:],
        [
            "url_length",
            "hostname_length",
            "digit_ratio",
            "html_bytes",
            "form_count",
            "iframe_count",
            "password_count",
            "sensitive_input",
        ],
    ):
        for label, g in df.groupby("label"):
            ax.hist(np.log1p(g[col]), bins=30, alpha=0.55, label=str(label))
        ax.set(title=col, xlabel="log(1+x)")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path / "train_distributions.png")
    plt.close(fig)
    corr = df[cols + ["label"]].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(12, 11))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(corr)), corr.columns, fontsize=7)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(path / "train_correlations.png")
    plt.close(fig)
    for name in ("train_distributions.png", "train_correlations.png"):
        publish(path / name, root / "results/figures" / name)
    report = runtime / "reports/eda/eda_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# EDA trên tập train",
        "",
        f"Số mẫu theo nhãn: {df.label.value_counts().to_dict()}.",
        f"SHA-256 split: {lock['sha256']}. Giao URL, domain và hash HTML giữa các tập bằng 0.",
        "Biểu đồ phân bố và ma trận Spearman nằm ở results/figures/.",
        "Ngoại lệ được đếm ngoài khoảng [Q1 − 1,5 IQR; Q3 + 1,5 IQR]. Đây là thống kê mô tả.",
        "",
        "| Biến | Thiếu | Ngoại lệ | Median lớp 0 | Median lớp 1 | Spearman với nhãn |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for c in cols:
        s = df[c]
        a, b = s.quantile([0.25, 0.75])
        out = ((s < a - 1.5 * (b - a)) | (s > b + 1.5 * (b - a))).sum()
        lines.append(
            f"| {c} | {s.isna().sum()} | {out} | {s[df.label == 0].median():.3g} | {s[df.label == 1].median():.3g} | {corr.loc[c, 'label']:.3f} |"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf8")
    publish(report, root / "reports/eda/eda_report.md")
    save_json(
        receipt,
        {"inputs": inputs, "outputs": {rel: sha256(root / rel) for rel in EDA_OUTPUTS}},
    )
    return root / EDA_OUTPUTS[0]
