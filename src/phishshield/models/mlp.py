from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from sklearn.preprocessing import StandardScaler


@dataclass
class FrozenMLP:
    scaler: StandardScaler
    weights: list
    training_device: str | None = None

    def predict_proba(self, x):
        w1, b1, w2, b2 = self.weights
        h = np.maximum(self.scaler.transform(x).astype("float32") @ w1.T + b1, 0)
        p = expit(h @ w2.T + b2).ravel()
        return np.column_stack([1 - p, p])


def fit(x, y, v, vy, seed, cfg, on_improvement, device):
    import random
    import torch
    from torch import nn
    from torch.utils.data import TensorDataset, DataLoader

    random.seed(seed)
    np.random.seed(seed)
    torch.random.default_generator.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    scaler = StandardScaler().fit(x)
    tensor = lambda a: torch.as_tensor(a, dtype=torch.float32)
    loader = DataLoader(
        TensorDataset(tensor(scaler.transform(x)), tensor(y)),
        batch_size=cfg["batch_size"],
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
    )
    vx, val_y = tensor(scaler.transform(v)).to(device), tensor(vy).to(device)
    layers = [nn.Linear(x.shape[1], cfg["hidden"]), nn.ReLU()]
    if cfg.get("dropout", 0):
        layers.append(nn.Dropout(cfg["dropout"]))
    layers.append(nn.Linear(cfg["hidden"], 1))
    net = nn.Sequential(*layers).to(device)
    if {parameter.device.type for parameter in net.parameters()} != {device}:
        raise RuntimeError(f"Tham số MLP chưa nằm trên thiết bị yêu cầu {device}.")
    opt = torch.optim.Adam(
        net.parameters(),
        lr=cfg["learning_rate"],
        weight_decay=cfg.get("weight_decay", 0),
    )
    loss_fn = nn.BCEWithLogitsLoss()
    history, best, stale = [], float("inf"), 0
    for epoch in range(cfg["epochs"]):
        net.train()
        total = 0
        for batch, target in loader:
            opt.zero_grad()
            loss = loss_fn(net(batch.to(device)).ravel(), target.to(device))
            loss.backward()
            opt.step()
            total += loss.item() * len(batch)
        net.eval()
        with torch.no_grad():
            current = loss_fn(net(vx).ravel(), val_y).item()
        history.append(dict(epoch=epoch + 1, loss=total / len(y), val_loss=current))
        if current < best:
            best, stale = current, 0
            frozen = FrozenMLP(
                scaler,
                [p.detach().cpu().numpy().copy() for p in net.parameters()],
                str(next(net.parameters()).device),
            )
            on_improvement(frozen, history)
        else:
            stale += 1
            if stale >= cfg["patience"]:
                break
    return history
