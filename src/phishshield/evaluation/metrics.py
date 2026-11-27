from sklearn import metrics as m


def scores(labels, probabilities, threshold):
    pred = probabilities >= threshold
    tn, fp, fn, tp = (
        int(x) for x in m.confusion_matrix(labels, pred, labels=[0, 1]).ravel()
    )
    precision, recall, _ = m.precision_recall_curve(labels, probabilities)
    return dict(
        accuracy=m.accuracy_score(labels, pred),
        precision=m.precision_score(labels, pred, zero_division=0),
        recall=m.recall_score(labels, pred, zero_division=0),
        f1=m.f1_score(labels, pred, zero_division=0),
        f2=m.fbeta_score(labels, pred, beta=2, zero_division=0),
        macro_f1=m.f1_score(labels, pred, average="macro", zero_division=0),
        roc_auc=m.roc_auc_score(labels, probabilities),
        pr_auc=m.auc(recall, precision),
        average_precision=m.average_precision_score(labels, probabilities),
        fpr=fp / (tn + fp),
        fnr=fn / (fn + tp),
        confusion_matrix=[[tn, fp], [fn, tp]],
    )


def choose(labels, probabilities, thresholds):
    return max(
        ((float(t), scores(labels, probabilities, t)) for t in thresholds),
        key=lambda pair: (
            pair[1]["f2"],
            pair[1]["precision"],
            -pair[1]["fpr"],
            pair[0],
        ),
    )
