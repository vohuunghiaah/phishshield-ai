"""Regenerate final tables and figures from verified, frozen inputs. Never fits a model."""
from pathlib import Path
import json
import shutil

import joblib
import numpy as np
import pandas as pd
import yaml
from phishshield.data.prepare import read_json
from phishshield.data.splits import connected_groups
from phishshield.evaluation.metrics import scores
from phishshield.training.runs import partitions
from final_audit import ROOT, OUT, audit
from final_features import FEATURES
from final_qc import checklist

TABLES = OUT / "tables"
FIG = OUT / "figures"


def generate():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    registry = []
    def table(num, name, data, source):
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        file = f"T{num:02}_{name}.csv"
        df.to_csv(TABLES/file, index=False, na_rep="NOT_AVAILABLE")
        registry.append(dict(id=f"T{num:02}",file=file,source=source,rows=len(df)))
    def csv(rel):
        return pd.read_csv(ROOT/rel)
    def read(rel):
        return read_json(ROOT/rel)
    data=read("manifests/dataset_manifest.json")
    table(1,"dataset",data["files"],"manifests/dataset_manifest.json")
    table(2,"data_audit",[data["audit"]],"manifests/dataset_manifest.json")
    frame=csv("data/processed/cohort.csv").merge(csv("data/splits/assignments.csv"),validate="one_to_one")
    frame["group"]=connected_groups(frame)
    table(3,"classes",frame.groupby(["split","label"]).size().rename("n").reset_index(),"cohort.csv × assignments.csv")
    fields=pd.DataFrame([line.split("|") for line in FEATURES.splitlines()],columns=["feature","type","definition","meaning","limitation"])
    fields["source"]=["src/phishshield/features/url_features.py"]*17+["src/phishshield/features/html_features.py"]*17
    assert list(fields.feature)==read("manifests/features.json")["schemas"]["url_html"]
    table(4,"dictionary",fields,"src/phishshield/features")
    split=frame.groupby("split").agg(rows=("serial_number","size"),groups=("group","nunique"),domains=("domain","nunique"))
    groups=frame.groupby(["split","group"]).size().groupby(level=0)
    split["largest_group"]=groups.max()
    split["median_group"]=groups.median()
    split["fraction"]=split.rows/len(frame)
    table(5,"splits",split.reset_index(),"locked split × connected_groups")
    cv=csv("data/splits/cv_folds.csv").merge(frame[["serial_number","label"]],validate="one_to_one")
    table(6,"folds",cv.groupby("fold").agg(rows=("label","size"),phishing=("label","sum"),phishing_fraction=("label","mean"),groups=("group","nunique")).reset_index(),"cv_folds.csv × cohort label")
    table(7,"hardware",pd.json_normalize(read_json(OUT/"hardware_software.json")),"run_manifest.json")
    baseline=yaml.safe_load((ROOT/"configs/models.yaml").read_text("utf8"))
    table(8,"baseline",[dict(model=m,parameter=k,value=v) for m,hp in baseline.items() for k,v in hp.items()],"configs/models.yaml; results/baseline_v1/effective_parameters.json")
    trial_frames=[]; settings=[]; spaces=[]; sweeps={}; locks={}
    for model in baseline:
        for mode in ("url_only","url_html"):
            path=Path("results/tuning_v2")/model/mode
            lock=read(path/"tuning_lock.json"); spec=lock["definition"]; locks[model,mode]=lock
            hp=spec["candidates"][spec["baseline_id"]]
            for k,v in hp.items():
                selected=lock["selected_hyperparameters"][k]
                options=spec["search_space"]["space"].get(k,[v])
                settings.append(dict(model=model,modality=mode,parameter=k,baseline=json.dumps(v),selected=json.dumps(selected),space=json.dumps(options),changed=v!=selected,trial=lock["selected_trial"],source=(path/"tuning_lock.json").as_posix()))
                if mode=="url_only": spaces.append(dict(model=model,parameter=k,space=json.dumps(options)))
            trial_frames.append(csv(path/"tuning_summary.csv").assign(model=model,modality=mode))
            sweeps[model,mode]=csv(path/"sensitivity.csv")
    table(9,"spaces",spaces,"configs/tuning/*.yaml")
    integ=csv("reports/final/experiment_integrity.csv")
    matrix=integ.groupby(["phase","model","modality"]).size().rename("records").reset_index()
    matrix["fold_evaluations"]=np.where(matrix.phase=="TUNING_V2",3*matrix.records,0)
    table(10,"matrix",matrix,"experiment_integrity.csv")
    base=csv("results/baseline_v1/validation.csv"); tuned=csv("results/comparisons/v2/per_seed.csv")
    keys=["model","modality"]; metrics=["f2","precision","recall","fpr","f1","accuracy","macro_f1","roc_auc","pr_auc","average_precision","fnr"]
    def stats(df):
        agg=df.groupby(keys)[metrics].agg(["mean","std","min","max"])
        agg.columns=["_".join(c) for c in agg.columns]; return agg.reset_index()
    table(11,"baseline_seeds",base,"results/baseline_v1/validation.csv")
    table(12,"baseline_summary",stats(base),"T11, sample SD")
    trials=pd.concat(trial_frames,ignore_index=True)
    table(13,"trials",trials,"6 × tuning_summary.csv, verified OOF")
    table(14,"parameters",settings,"6 × tuning_lock.json")
    table(15,"tuned_seeds",tuned,"results/comparisons/v2/per_seed.csv")
    table(16,"tuned_summary",stats(tuned),"T15, sample SD")
    paired=base.merge(tuned,on=keys+["seed"],suffixes=("_v1","_v2"),validate="one_to_one")
    long=pd.concat([paired[keys+["seed"]].assign(metric=k,v1=paired[k+"_v1"],v2=paired[k+"_v2"]) for k in metrics])
    long["delta"]=long.v2-long.v1; long["delta_pp"]=100*long.delta
    table(17,"paired_seeds",long,"T11 × T15 on seed")
    both=pd.concat([base.assign(phase="Baseline"),tuned.assign(phase="Tuned")])
    ab=[]
    for (phase,model),subset in both.groupby(["phase","model"]):
        for k in metrics:
            p=subset.pivot(index="seed",columns="modality",values=k); delta=p.url_html-p.url_only
            ab.append(dict(phase=phase,model=model,metric=k,url_only=p.url_only.mean(),url_html=p.url_html.mean(),
                           delta=delta.mean(),delta_pp=100*delta.mean(),relative_percent=100*delta.mean()/p.url_only.mean(),sample_sd=delta.std()))
    table(18,"ablation",ab,"T11 and T15, paired by seed")
    stats_pair=long.groupby(keys+["metric"]).agg(n=("delta","size"),mean_delta=("delta","mean"),sd=("delta","std"),minimum=("delta","min"),maximum=("delta","max"),baseline=("v1","mean"),tuned=("v2","mean")).reset_index()
    stats_pair["pp"]=100*stats_pair.mean_delta; stats_pair["relative_percent"]=stats_pair.pp/stats_pair.baseline
    table(19,"paired_statistics",stats_pair,"T17")
    sel=read("manifests/model_selection_v2.json")
    table(20,"selection",[dict(role=k,**sel[k]) for k in ("primary","url_fallback")],"model_selection_v2.json")
    test=read("results/metrics/locked_test.json")["metrics"]
    table(21,"test_metrics",[dict(metric=k,value=v) for k,v in test.items() if k!="confusion_matrix"],"locked_test.json verified from locked_test.csv")
    table(22,"confusion",pd.DataFrame(test["confusion_matrix"],columns=["pred_0","pred_1"]).assign(actual=[0,1]),"locked_test.csv")
    table(23,"shap",csv("results/explanations/importance.csv"),"24 Validation SHAP contributions")
    pred=csv("results/predictions/locked_test.csv").merge(csv("data/features/url_html/features.csv"),validate="one_to_one")
    pred["outcome"]=np.select([(pred.label==1)&(pred.prediction==0),(pred.label==0)&(pred.prediction==1),pred.label==1],["FN","FP","TP"],default="TN")
    pred["distance"]=abs(pred.probability-sel["primary"]["threshold"])
    table(24,"error_cases",pred.sort_values("distance"),"locked_test.csv × locked url_html features; serial IDs only")
    cost=[]
    for r in integ[integ.phase!="TUNING_V2"].itertuples():
        m=read(r.path)
        cost.append(dict(phase=r.phase,model=r.model,modality=r.modality,seed=r.seed,device=r.device,
                         checkpoint_bytes=(ROOT/m["checkpoint"]).stat().st_size,training_seconds=m.get("training_seconds"),
                         inference_ms_per_row=m.get("inference_ms_per_row"),start=m["start"],end=m["end"]))
    table(25,"cost",cost,"Run manifests; V1 fit-only timing unavailable")
    limits=[("External validity","Một corpus; chưa kiểm thử bên ngoài"),("Thời gian","Chưa có temporal split hoặc drift benchmark"),("Leakage","Near duplicates/campaign chưa có kiểm tra đầy đủ"),("Seed","Ba seed chung một split"),("Search","24 candidate, một seed"),("MLP","Inner stopping giảm số hàng fit"),("Vận hành","FP đáng kể; fallback chưa chấm Test"),("Calibration","Điểm chưa hiệu chuẩn độc lập"),("Attribution","Tương quan, phụ thuộc nền và thứ tự"),("Triển khai","Demo loopback, chưa benchmark tải hay egress")]
    table(26,"limitations",pd.DataFrame(limits,columns=["threat","scope"]),"Protocol V2 and frozen evaluation scope")
    table(27,"qc",checklist(ROOT,OUT),"final_audit.py, HTTP evidence, pytest, UI screenshots and deployment guide")
    checks=read_json(OUT/"artifact_checksums.json")
    families = [
        ("data/raw/", "CompPhish input", "CompPhish v4", "01–02 data preparation", "4"),
        ("data/processed/", "Shared cohort", "data/prepare.py", "features and group split", "4"),
        ("data/features/", "Feature matrix", "features/pipeline.py", "training/runs.py", "1.0.0"),
        ("data/splits/", "Frozen assignments", "data/splits.py, tuning/design.py", "training and CV audit", "V1/V2"),
        ("results/tuning_v2/", "Candidate evidence", "tuning/search.py", "tuning/reporting.py, audit", "TUNING_V2"),
        ("results/tuned_v2/", "Refit evidence", "training/runs.py, tuning/reporting.py", "evaluation/compare.py", "TUNED_V2"),
        ("results/baseline_v1/", "Historical comparison", "training/runs.py", "V1/V2 comparison", "BASELINE_V1"),
        ("checkpoints/selected_model/", "Inference bundle or selection", "evaluation/compare.py", "API, SHAP", "TUNED_V2"),
        ("checkpoints/tuned_v2/", "Refit checkpoint", "training/runs.py", "selection and replay", "TUNED_V2"),
        ("checkpoints/", "Baseline checkpoint", "training/runs.py", "Validation replay", "BASELINE_V1"),
        ("results/explanations/", "SHAP evidence", "explainability/report.py", "explanation audit", "TUNED_V2"),
        ("results/metrics/", "Frozen Test metrics", "evaluation/compare.py", "API and final report", "TUNED_V2"),
        ("results/predictions/", "Frozen Test predictions", "evaluation/compare.py", "Test metrics and error analysis", "TUNED_V2"),
        ("manifests/", "Provenance and decisions", "workflow and leader approval", "final audit and selection", "V1/V2"),
        ("results/", "Run or diagnostic evidence", "scientific workflow", "final audit and reporting", "V1/V2"),
    ]
    def entry(path, checksum):
        meta = next((r[1:] for r in families if path.startswith(r[0])), ("Scientific input", "workflow 00–12", "scientific audit", "V1/V2"))
        return dict(path=path, sha256=checksum, **dict(zip(("purpose","producer","consumer","version"),meta)))
    table(28,"registry",[entry(k,v) for k,v in checks.items()],"artifact_checksums.json")
    pd.DataFrame(registry).to_csv(TABLES/"index.csv",index=False)
    from final_figures import figures
    figures(ROOT, OUT, frame, cv, both, trials, sweeps, pred, locks, sel)


if __name__=="__main__":
    audit()
    generate()

