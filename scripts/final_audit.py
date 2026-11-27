"""Read-only verification of CompPhish data, frozen training records and predictions."""
import hashlib
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from phishshield.data.prepare import read_json
from phishshield.data.splits import connected_groups
from phishshield.evaluation.metrics import scores
from phishshield.features.pipeline import extract_features, schema
from phishshield.training.runs import partitions
from phishshield.tuning.design import digest, folds as group_folds, winner
from phishshield.tuning.search import definition
from phishshield.utils.storage import sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/final"


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", "utf8")


def near(metrics, original, tol=1e-9):
    for key, value in metrics.items():
        np.testing.assert_allclose(value, original[key], atol=tol, rtol=0, err_msg=key)


def verify_threshold(labels, probabilities, thresholds, expected):
    y = np.asarray(labels, dtype=bool)
    def rank(t):
        predicted = np.asarray(probabilities) >= t
        tp = int((predicted & y).sum())
        fp = int((predicted & ~y).sum())
        fn = int((~predicted & y).sum())
        return (5*tp/(5*tp+4*fn+fp), tp/max(tp+fp,1), -fp/int((~y).sum()), t)
    assert max(thresholds, key=rank) == expected


def audit():
    OUT.mkdir(exist_ok=True, parents=True)
    hashes = {}
    inventory = []

    def check(rel, expected=None):
        path = ROOT / rel
        value = sha256(path)
        if expected and value != expected:
            raise ValueError(f"Checksum mismatch: {rel}")
        hashes[path.relative_to(ROOT).as_posix()] = value
        return value

    def load(rel):
        check(rel)
        return read_json(ROOT / rel)

    dataset = load("manifests/dataset_manifest.json")
    for item in dataset["files"]:
        check("data/raw/compphish/" + item["name"], item["sha256"])
    features = load("manifests/features.json")
    for rel, value in features["artifacts"].items():
        check(rel, value)
    for rel, value in load("manifests/eda.json")["outputs"].items():
        check(rel, value)
    lock = load("data/splits/lock.json")
    check("data/splits/assignments.csv", lock["sha256"])
    cvlock = load("manifests/cv_lock.json")
    check("data/splits/cv_folds.csv", cvlock["sha256"])
    cv = pd.read_csv(ROOT / "data/splits/cv_folds.csv").set_index("serial_number").sort_index()
    frame = pd.read_csv(ROOT / "data/processed/cohort.csv").merge(
        pd.read_csv(ROOT / "data/splits/assignments.csv"), validate="one_to_one")
    frame["group"] = connected_groups(frame)
    for key in ("group", "url", "domain", "html_sha256"):
        assert frame.groupby(key).split.nunique().max() == 1
    assert cv.groupby("group").fold.nunique().max() == 1
    train = frame[frame.split == "train"].set_index("serial_number").sort_index()
    assert cv.index.equals(train.index)
    assert train.assign(fold=cv.fold).groupby("group").fold.nunique().max() == 1
    selection = load("manifests/model_selection_v2.json")
    approval = load("manifests/project_leader_approval.json")
    assert approval["selection_sha256"] == hashes["manifests/model_selection_v2.json"]
    assert approval["decision"] == "APPROVED" and approval["reviewer"] and approval["validation_comparison_reviewed"] is True
    for path, value in selection["artifacts"].items():
        check(path, value)
    val = {m: partitions(ROOT,m,["validation"])["validation"] for m in features["schemas"]}
    sampled = frame[frame.split=="validation"].sample(24,random_state=42)
    with zipfile.ZipFile(ROOT/"data/raw/compphish/All_HTML.zip") as archive:
        for row in sampled.itertuples():
            payload = archive.read(f"All_HTML/{row.serial_number}.txt")
            assert hashlib.sha256(payload).hexdigest()==row.html_sha256
            try:
                html = payload.decode("utf-8-sig")
            except UnicodeDecodeError:
                html = payload.decode("cp1252",errors="replace")
            for mode, snapshot in (("url_html",html),("url_only",None)):
                fresh = extract_features(row.url,snapshot)
                stored = val[mode].loc[val[mode].serial_number==row.serial_number,schema(mode)]
                assert list(fresh)==schema(mode)
                np.testing.assert_allclose(list(fresh.values()),stored.iloc[0].to_numpy(),rtol=1e-12,atol=1e-12)
    grid = read_json(ROOT/"results/tuning_v2/random_forest/url_html/tuning_lock.json")["definition"]["protocol"]["thresholds"]
    scaler_moments = {}
    for mode in val:
        tr = partitions(ROOT, mode, ["train"])["train"].merge(cv.reset_index(), on="serial_number", validate="one_to_one")
        cols = schema(mode)
        def moments(data):
            x = data[cols].to_numpy()
            return (len(x), x.mean(axis=0), x.var(axis=0))
        scaler_moments[mode,None] = moments(tr)
        for fold in range(3):
            outer = tr[tr.fold != fold]
            inner = group_folds(outer, 3, 2026)
            scaler_moments[mode,fold] = moments(outer[inner.fold != 0])
    def verify_scaler(estimator, expected):
        size, mean, variance = expected
        scaler = estimator.scaler
        assert scaler.n_samples_seen_ == size
        np.testing.assert_allclose(scaler.mean_, mean, rtol=1e-7, atol=1e-10)
        np.testing.assert_allclose(scaler.var_, variance, rtol=1e-7, atol=1e-10)
    preds = {}
    hardware = []
    for phase, registry in [("BASELINE_V1","baseline_v1"),("TUNED_V2","tuned_v2")]:
        entries = load(f"manifests/{registry}.json")["runs"]
        assert len({(r["model"],r["modality"],r["seed"]) for r in entries}) == len(entries) == 18
        for r in entries:
            path = Path(r.get("manifest",r.get("path")))
            check(path,r.get("manifest_sha256",r.get("sha256")))
            m = read_json(ROOT/path)
            model, mode, seed = (m[k] for k in ("model","modality","seed"))
            assert [model,mode,seed] == [r[k] for k in ("model","modality","seed")]
            assert m["status"] == "COMPLETED" and m["dataset_version"] == 4 and m["feature_version"] == "1.0.0" and m["split_hash"] == lock["sha256"]
            for name in ("config","metrics"):
                check(path.parent/(name+".json"), m[name+"_sha256"])
            if r.get("history_sha256"):
                check(path.parent/"history.json",r["history_sha256"])
            check(m["checkpoint"],m["checkpoint_sha256"])
            b=joblib.load(ROOT/m["checkpoint"])
            assert b["columns"] == schema(mode) and b["model"]==model and b["modality"]==mode
            pred=b["estimator"].predict_proba(val[mode][schema(mode)].to_numpy())[:,1]
            near(scores(val[mode].label,pred,m["threshold"]),m["metrics"],1e-5)
            verify_threshold(val[mode].label,pred,grid,m["threshold"])
            if model=="mlp":
                verify_scaler(b["estimator"],scaler_moments[mode,None])
            row=dict(phase=phase,model=model,modality=mode,seed=seed,path=path.as_posix(),status="VERIFIED",
                     checkpoint=m["checkpoint"],device=m["device"],threshold=m["threshold"],attempt=m["attempt"])
            if model=="xgboost":
                booster=b["estimator"].get_booster()
                row.update(trees_sha256=hashlib.sha256("\n".join(booster.get_dump()).encode()).hexdigest(),
                           val_probability_sha256=hashlib.sha256(pred.tobytes()).hexdigest())
            inventory.append(row)
            hardware.append(dict(phase=phase,model=model,modality=mode,seed=seed,hardware=m["hardware"],software=m["software"]))
            if phase=="TUNED_V2":
                bind=Path("results/tuning_v2")/model/mode/"tuning_lock.json"
                assert m["tuning_lock_sha256"]==hashes[bind.as_posix()]
                assert m["hyperparameters"]==read_json(ROOT/bind)["selected_hyperparameters"]
            preds[(phase,model,mode,seed)] = pred
    tasks=[]
    for model in ("random_forest","xgboost","mlp"):
        for mode in features["schemas"]:
            folder=Path("results/tuning_v2")/model/mode
            frozen=read_json(ROOT/folder/"tuning_lock.json")
            spec=definition(ROOT,model,mode)
            assert frozen["definition"]==spec and len(frozen["trial_manifests"])==24
            assert set(frozen["trial_manifests"])==set(spec["candidates"])
            for name,v in frozen["artifacts"].items():
                check(folder/name,v)
            for cid,hp in spec["candidates"].items():
                tasks.append((folder/cid,frozen["trial_manifests"][cid],hp,spec))

    def trial(item):
        folder, expected, hp, spec=item
        path=folder/"trial_manifest.json"
        check(path,expected)
        m=read_json(ROOT/path)
        assert m["trial_id"]==folder.name and m["identity"]==digest(spec) and m["hyperparameters"]==hp
        assert m["model"]==spec["model"] and m["modality"]==spec["modality"] and m["phase"]==spec["phase"]
        assert m["training_seed"]==42 and m["cv_hash"]==cvlock["sha256"] and m["status"]=="COMPLETED"
        for name,value in m["artifacts"].items():
            check(folder/name,value)
            if name.endswith(".joblib"):
                bundle=joblib.load(ROOT/folder/name)
                assert bundle["columns"]==schema(m["modality"]) and bundle["architecture"]==hp
                fold_number = int(Path(name).stem.split("_")[-1])
                verify_scaler(bundle["estimator"],scaler_moments[m["modality"],fold_number])
        oof=pd.read_parquet(ROOT/folder/"oof_predictions.parquet").set_index("serial_number").sort_index()
        assert oof.index.equals(cv.index) and oof.fold.equals(cv.fold) and oof.label.equals(train.label)
        met=read_json(ROOT/folder/"trial_metrics.json")
        near(scores(oof.label,oof.probability,met["threshold"]),met)
        verify_threshold(oof.label,oof.probability,spec["protocol"]["thresholds"],met["threshold"])
        np.testing.assert_allclose(log_loss(oof.label,oof.probability),met["log_loss"])
        folds=read_json(ROOT/folder/"fold_metrics.json")
        assert sorted(f["fold"] for f in folds)==[0,1,2]
        for f in folds:
            part=oof[oof.fold==f["fold"]]
            assert len(part)==f["rows"]
            near(scores(part.label,part.probability,met["threshold"]),f["metrics_at_pooled_threshold"])
        return dict(phase=m["phase"],model=m["model"],modality=m["modality"],seed=42,trial=m["trial_id"],
                    folds=3,device=m["device"],path=path.as_posix(),status="VERIFIED",threshold=met["threshold"],
                    f2=met["f2"],precision=met["precision"],fpr=met["fpr"],checkpoint="3 fold files" if m["model"]=="mlp" else "temporary during CV")
    with ThreadPoolExecutor(max_workers=6) as pool:
        inventory.extend(pool.map(trial,tasks))
    for model,mode in {(t[3]["model"],t[3]["modality"]) for t in tasks}:
        frozen=read_json(ROOT/"results/tuning_v2"/model/mode/"tuning_lock.json")
        rows=[dict(trial_id=r["trial"],**r) for r in inventory if r["phase"]=="TUNING_V2" and r["model"]==model and r["modality"]==mode]
        assert winner(rows,frozen["definition"]["baseline_id"])["trial_id"]==frozen["selected_trial"]
    for role in ("primary","url_fallback"):
        info=selection[role]
        assert info==load(f"checkpoints/selected_model/{role}/selection.json")
        check(info["artifact"],info["checkpoint_sha256"])
    tuned = [read_json(ROOT / row["path"]) for row in inventory if row["phase"] == "TUNED_V2"]
    ranked = pd.DataFrame([{**m["metrics"], **{k:m[k] for k in ("model","modality","seed","checkpoint_sha256","threshold")}} for m in tuned])
    means = ranked.groupby(["model","modality"], as_index=False)[["f2","precision","fpr"]].mean()
    for role, eligible in (("primary", means), ("url_fallback", means[means.modality=="url_only"])):
        first = eligible.sort_values(["f2","precision","fpr","model","modality"], ascending=[False,False,True,True,True]).iloc[0]
        candidates = ranked[(ranked.model==first.model)&(ranked.modality==first.modality)]
        best = candidates.sort_values(["f2","precision","fpr","seed"], ascending=[False,False,True,True]).iloc[0]
        assert all(selection[role][key]==best[key] for key in ("model","modality","seed","threshold","checkpoint_sha256"))
    result=load("results/metrics/locked_test.json")
    testpath="results/predictions/locked_test.csv"
    check(testpath)
    test=pd.read_csv(ROOT/testpath,float_precision="round_trip").set_index("serial_number").sort_index()
    labels=frame[frame.split=="test"].set_index("serial_number").label.sort_index()
    assert test.label.equals(labels) and result["selection"]==selection["primary"]
    threshold=result["selection"]["threshold"]
    assert np.array_equal(test.prediction, test.probability>=threshold)
    near(scores(test.label,test.probability,threshold),result["metrics"])
    info=selection["primary"]
    est=joblib.load(ROOT/info["artifact"])["estimator"]
    mode=info["modality"]
    trainval=partitions(ROOT,mode,["train","validation"])
    cols=schema(mode)
    bg=trainval["train"].sample(32,random_state=42)
    sample=trainval["validation"].sample(24,random_state=42)
    for name in ("importance.csv","contributions.csv","local_vi.json","shap_summary.png","shap_local.png"):
        check("results/explanations/"+name)
    shap=pd.read_csv(ROOT/"results/explanations/contributions.csv")
    local=read_json(ROOT/"results/explanations/local_vi.json")
    assert list(shap.columns)==["serial_number",*cols] and list(shap.serial_number)==list(sample.serial_number)
    base=est.predict_proba(bg[cols].to_numpy())[:,1].mean()
    scores_val=est.predict_proba(sample[cols].to_numpy())[:,1]
    np.testing.assert_allclose(base,local["base"],atol=1e-7)
    np.testing.assert_allclose(base+shap[cols].sum(axis=1),scores_val,atol=1e-6)
    importance=pd.read_csv(ROOT/"results/explanations/importance.csv").set_index("feature").loc[cols]
    np.testing.assert_allclose(importance.mean_abs_shap,shap[cols].abs().mean(),atol=1e-8)
    assert local["serial_number"]==int(sample.iloc[0].serial_number) and abs(scores_val[0]-local["score"])<1e-7
    dates={rel: (ROOT/rel).stat().st_mtime for rel in ("manifests/model_selection_v2.json","manifests/project_leader_approval.json","results/metrics/locked_test.json")}
    dump(OUT/"audit_summary.json",dict(runs=36,trials=len(tasks),folds=sum(r.get("folds",0) for r in inventory),
        hashes=len(hashes),test_rows=len(test),shap_rows=len(shap),shap_max_residual=float(np.max(np.abs(base+shap[cols].sum(axis=1)-scores_val))),
        chronology_by_mtime=dates,source_mtime_order=list(dates.values())==sorted(dates.values())))
    pd.DataFrame(inventory).to_csv(OUT/"experiment_integrity.csv",index=False)
    dump(OUT/"artifact_checksums.json",dict(sorted(hashes.items())))
    dump(OUT/"hardware_software.json",hardware)
    return frame,preds,val


if __name__=="__main__":
    audit()

