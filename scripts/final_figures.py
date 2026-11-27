"""Publication figures. Diagrams are explicitly distinguished from measured plots."""
import json
import shutil
from textwrap import fill
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve
from phishshield.training.runs import partitions
from phishshield.evaluation.metrics import scores


def figures(root, out, frame, cv, both, trials, sweeps, pred, locks, selection):
    folder=out/"figures"; index=[]
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
        "axes.spines.right":False,"axes.titlelocation":"left","axes.prop_cycle":plt.cycler(color=["#146a6b","#aa5032","#506692","#806093"])})
    def axes(title):
        fig,ax=plt.subplots(figsize=(7.9,4),layout="constrained"); ax.set_title(title,pad=14)
        return fig,ax
    def finish(fig,i,name,title):
        stem=f"F{i:02}_{name}"
        for ext in ("png","svg"):
            fig.savefig(folder/(stem+"."+ext),dpi=190,bbox_inches="tight")
        plt.close(fig); index.append((i,stem+".png",title))
    def copy(i,src,title):
        stem=f"F{i:02}_"+src.stem+".png"; shutil.copyfile(src,folder/stem);index.append((i,stem,title))
    def flow(i,name,title,nodes):
        fig,ax=axes(title+" · sơ đồ minh họa")
        fig.set_size_inches(8,2.8); ax.axis("off"); xs=np.linspace(.115,.885,len(nodes))
        for j,(x,label) in enumerate(zip(xs,nodes)):
            ax.text(x,.5,fill(label,15),ha="center",va="center",transform=ax.transAxes,
                    bbox=dict(boxstyle="round,pad=.55",fc="#ecf4f3",ec="#22716f"),fontsize=10)
            if j+1<len(nodes):
                ax.annotate("",xy=(xs[j+1]-.091,.5),xytext=(x+.091,.5),xycoords="axes fraction",arrowprops=dict(arrowstyle="->",color="#334b52"))
        finish(fig,i,name,title)
    flow(1,"pipeline","Đường đi của dữ liệu",["CompPhish v4","Cohort ghép cặp","Split theo nhóm","Tuning và Validation","Test đã khóa"])
    flow(2,"preprocessing","Kiểm định và làm sạch",["15.358 mapping","Ghép snapshot theo ID","Loại 31 mẫu","15.327 cặp hợp lệ"])
    fig,ax=axes("Phân bố lớp theo tập"); pd.crosstab(frame.split,frame.label).reindex(["train","validation","test"]).rename(columns={0:"Legitimate",1:"Phishing"}).plot.bar(ax=ax,rot=0)
    ax.set(xlabel="",ylabel="Số mẫu"); finish(fig,3,"classes","Phân bố lớp")
    copy(4,root/"results/figures/train_distributions.png","Phân bố trên Train")
    copy(5,root/"results/figures/train_correlations.png","Tương quan Spearman trên Train")
    flow(6,"groups","Gom nhóm và khóa split",["Domain + SHA HTML","Hợp thành phần liên thông","Xếp nhóm lớn trước","Gán nguyên nhóm"])
    flow(7,"search","Đánh giá candidate",["24 candidate","3 fold trên Train","Gộp OOF và chọn ngưỡng","Khóa cấu hình"])
    flow(8,"forest","Random Forest chính",["34 đặc trưng","Bootstrap từng cây","300 cây CART","Trung bình điểm lá","Ngưỡng 0,20"])
    flow(9,"boosting","Boosting tuần tự",["Logit ban đầu","Gradient và Hessian","Cây hist tối ưu gain","Cộng η × cây","Sigmoid"])
    flow(10,"mlp","MLP baseline và tuned",["17 hoặc 34 đầu vào","StandardScaler trên fit","Dense 64 → ReLU (V2: 256)","Dropout nếu p > 0","Dense 1 → sigmoid"])
    for i,model,axis in [(11,"random_forest","n_estimators"),(12,"xgboost","n_estimators"),(13,"mlp","hidden")]:
        fig,ax=axes("Độ nhạy OOF khi giữ các tham số còn lại ở baseline")
        for mode in ("url_only","url_html"):
            d=sweeps[model,mode].sort_values(axis); ax.plot(d[axis],d.f2,"o-",label=mode)
        ax.set(xlabel=model+" · "+axis,ylabel="F2 pooled OOF"); ax.legend();finish(fig,i,model+"_sweep","Controlled sweep "+model)
    fig,ax=axes("MLP Tuned V2 · URL+HTML · seed 42")
    path=root/"results/tuned_v2/mlp/url_html/seed_42/history.json"
    h=pd.DataFrame(json.loads(path.read_text("utf8")))
    ax.plot(h.epoch,h.loss,label="Train");ax.plot(h.epoch,h.val_loss,label="Validation")
    ax.set(xlabel="Epoch",ylabel="BCE");ax.legend();finish(fig,14,"loss","Loss theo epoch")
    labels={"random_forest":"RF","xgboost":"XGB","mlp":"MLP"}
    both=both.copy()
    both["pair"]=[labels[m]+"/"+("URL" if s=="url_only" else "HTML") for m,s in zip(both.model,both.modality)]
    for i,k,phase in [(15,"f2","Baseline"),(16,"f2","Tuned"),(17,"f2",None),(18,"fpr",None),(19,"f2",None)]:
        title=(phase or "Baseline và Tuned")+" · Validation"
        fig,ax=axes(title); d=both if phase is None else both[both.phase==phase]
        agg=d.groupby(["pair","phase"])[k]; mean=agg.mean().unstack(); sd=agg.std().unstack()
        mean.plot.bar(ax=ax,yerr=sd if i==19 else None,capsize=3,rot=18)
        ax.set(xlabel="",ylabel=k.upper());ax.legend(title=None);finish(fig,i,k+"_"+str(i),title)
    fig,ax=axes("Chênh lệch F2 khi bổ sung HTML · Validation")
    a=pd.read_csv(out/"tables/T18_ablation.csv");a=a[a.metric=="f2"].pivot(index="model",columns="phase",values="delta_pp")
    a.plot.bar(ax=ax,rot=0);ax.set(ylabel="Điểm phần trăm",xlabel="");finish(fig,20,"ablation","Ablation theo modality")
    info=selection["primary"]; est=joblib.load(root/info["artifact"])
    val=partitions(root,info["modality"],["validation"])["validation"]; p=est["estimator"].predict_proba(val[est["columns"]].to_numpy())[:,1]
    curve=pd.DataFrame([dict(t=t,**scores(val.label,p,t)) for t in np.arange(1,20)/20]);curve.drop(columns="confusion_matrix").to_csv(out/"tables/validation_thresholds.csv",index=False)
    fig,ax=axes("Ngưỡng của RF chính · Validation, seed 43")
    for k in ("f2","precision","recall","fpr"):ax.plot(curve.t,curve[k],label=k)
    ax.axvline(info["threshold"],ls=":",color="black");ax.set(xlabel="Ngưỡng",ylabel="Tỷ lệ");ax.legend();finish(fig,21,"threshold","Ngưỡng trên Validation")
    for i,name in [(22,"PR"),(23,"ROC")]:
        fig,ax=axes(name+" · Random Forest URL+HTML · Locked Test")
        if i==22:
            precision,recall,_=precision_recall_curve(pred.label,pred.probability);ax.plot(recall,precision);ax.set(xlabel="Recall",ylabel="Precision")
        else:
            fpr,tpr,_=roc_curve(pred.label,pred.probability);ax.plot(fpr,tpr);ax.plot([0,1],[0,1],":",color="gray");ax.set(xlabel="FPR",ylabel="TPR")
        finish(fig,i,name,name+" trên Locked Test")
    fig,ax=axes("Ma trận nhầm lẫn · Locked Test")
    cm=pd.crosstab(pred.label,pred.prediction).to_numpy(); ax.imshow(cm,cmap="GnBu")
    for (y,x),v in np.ndenumerate(cm):ax.text(x,y,str(v),va="center",ha="center",color="white" if v>600 else "black",fontsize=16)
    ax.set(xticks=[0,1],yticks=[0,1],xlabel="Dự đoán",ylabel="Nhãn thật");finish(fig,24,"confusion","Ma trận Test")
    for i,name in [(25,"summary"),(26,"local")]:copy(i,root/f"results/explanations/shap_{name}.png","SHAP trên Validation")
    cost=pd.read_csv(out/"tables/T25_cost.csv",na_values=["NOT_AVAILABLE"]).query("phase == 'TUNED_V2'")
    measured=both[both.phase=="Tuned"].merge(cost[["model","modality","seed","checkpoint_bytes","training_seconds"]],on=["model","modality","seed"],validate="one_to_one")
    for i,k in [(27,"checkpoint_bytes"),(28,"training_seconds")]:
        fig,ax=axes("Chi phí và F2 trung bình · Tuned Validation")
        for pair,d in measured.groupby("pair"):ax.scatter(d[k].mean(),d.f2.mean(),label=pair)
        ax.set(xlabel=k,ylabel="F2");ax.legend(fontsize=8,ncol=2);finish(fig,i,k,"Chi phí theo cặp")
    flow(29,"deployment","Kiến trúc local",["Streamlit","FastAPI loopback","Xác minh checkpoint","Trích đặc trưng","RF và giải thích"])
    flow(30,"sequence","Một yêu cầu phân tích",["Nhập URL / HTML","POST JSON","Chọn modality","Tính điểm và ngưỡng","Hiển thị kết quả"])
    pd.DataFrame(sorted(index),columns=["id","file","title"]).to_csv(folder/"index.csv",index=False)

