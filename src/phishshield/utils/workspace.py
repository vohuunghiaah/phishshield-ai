from phishshield.training.runs import MEMBERS
from phishshield.data.prepare import FEATURES

DIRECTORIES = [
    "notebooks",
    "configs",
    "data/raw/compphish",
    "data/interim",
    "data/processed",
    "data/splits",
    "scripts",
    "tests",
    "docs",
    "manifests",
    "logs",
    *("data/features/" + m for m in FEATURES),
    *(
        "experiments/" + member + "/" + m
        for member in MEMBERS.values()
        for m in FEATURES
    ),
    *("checkpoints/" + m for m in [*MEMBERS, "selected_model"]),
    *(
        "results/" + n
        for n in ["metrics", "predictions", "comparisons", "explanations", "figures"]
    ),
    *("reports/" + n for n in ["setup", "dataset", "eda", "experiments", "final"]),
]


def initialize(root):
    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
