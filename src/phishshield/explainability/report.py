import os

os.environ["MPLBACKEND"] = "Agg"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from phishshield.inference.service import selected
from phishshield.training.runs import partitions
from phishshield.data.prepare import save_frame
from phishshield.utils.storage import publish, save_json


def explain(root, runtime):
    meta, bundle = selected(root, "primary")
    d = partitions(root, meta["modality"], ["train", "validation"])
    cols = bundle["columns"]
    bg = d["train"][cols].sample(min(32, len(d["train"])), random_state=42)
    val = d["validation"].sample(min(24, len(d["validation"])), random_state=42)
    # Model-agnostic SHAP computes all three models on the same phishing probability scale.
    pred = lambda x: bundle["estimator"].predict_proba(np.asarray(x))[:, 1]
    explainer = shap.Explainer(
        pred, bg, algorithm="permutation", seed=42, feature_names=cols
    )
    s = explainer(val[cols], max_evals=3 * (2 * len(cols) + 1))
    out = "results/explanations/"
    frame = pd.DataFrame(s.values, columns=cols)
    frame.insert(0, "serial_number", val.serial_number.to_numpy())
    save_frame(frame, out + "contributions.csv", root, runtime)
    save_frame(
        pd.DataFrame(
            {"feature": cols, "mean_abs_shap": np.abs(s.values).mean(axis=0)}
        ).sort_values("mean_abs_shap", ascending=False),
        out + "importance.csv",
        root,
        runtime,
    )
    for name, plot in [
        ("summary", lambda: shap.plots.beeswarm(s, show=False)),
        ("local", lambda: shap.plots.waterfall(s[0], show=False)),
    ]:
        plot()
        path = runtime / f"shap_{name}.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        publish(path, root / out / path.name)
    idx = np.argsort(-np.abs(s.values[0]))[:5]
    lines = [
        f"Đặc trưng {cols[i]} có giá trị {val.iloc[0][cols[i]]:.3g}, làm {'tăng' if s.values[0, i] >= 0 else 'giảm'} điểm phishing {abs(s.values[0, i]):.3f} so với nền train."
        for i in idx
    ]
    save_json(
        root / out / "local_vi.json",
        dict(
            serial_number=int(val.iloc[0].serial_number),
            background="train",
            base=float(s.base_values[0]),
            score=float(pred(val[cols].iloc[:1])[0]),
            explanation=lines,
        ),
    )
    return lines
