"""SER training loop with checkpointing and evaluation."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from ser.core.registry import HUB_IDS, build_collator, build_model
from ser.core.seed import set_seed
from ser.data.class_weights import compute_class_weights
from ser.data.torch_dataset import RAVDESSSERDataset
from ser.evaluation.plots import plot_training_curves
from ser.evaluation.runner import evaluate_split, save_split_results
from ser.training.experiment import create_experiment_dirs
from ser.data.dataset import load_ravdess_splits
from ser.data.labels import EMOTION_TO_ID
from ser.data.split import assert_no_actor_leakage

from ser.core.config import save_config

logger = logging.getLogger(__name__)


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _param_groups(model: torch.nn.Module, cfg: Dict[str, Any]) -> List[Dict]:
    enc_lr = float(cfg.get("encoder_learning_rate", 1e-5))
    head_lr = float(cfg.get("classifier_learning_rate", 1e-4))
    wd = float(cfg.get("weight_decay", 0.01))

    if hasattr(model, "encoder") and hasattr(model, "classifier"):
        encoder_params = [p for p in model.encoder.parameters() if p.requires_grad]
        head_params = [
            p for n, p in model.named_parameters()
            if p.requires_grad and not n.startswith("encoder.")
        ]
        groups = []
        if encoder_params:
            groups.append({"params": encoder_params, "lr": enc_lr, "weight_decay": wd})
        if head_params:
            groups.append({"params": head_params, "lr": head_lr, "weight_decay": wd})
        return groups or [{"params": model.parameters(), "lr": head_lr, "weight_decay": wd}]

    lr = float(cfg.get("learning_rate", 1e-3))
    return [{"params": model.parameters(), "lr": lr, "weight_decay": wd}]


def _train_step(model, batch, device, class_weights, scaler, accum_steps):
    labels = batch["labels"].to(device)
    cw = class_weights.to(device) if class_weights is not None else None
    kw = {"labels": labels, "class_weights": cw}
    mask = batch.get("attention_mask")
    if mask is not None:
        mask = mask.to(device)
    if "input_values" in batch:
        inputs = {"input_values": batch["input_values"].to(device), "attention_mask": mask}
    else:
        inputs = {"mfcc": batch["mfcc"].to(device), "attention_mask": mask}

    use_amp = scaler is not None
    with torch.cuda.amp.autocast(enabled=use_amp):
        out = model(**inputs, **kw)
        loss = out["loss"] / accum_steps

    if use_amp:
        scaler.scale(loss).backward()
    else:
        loss.backward()

    with torch.no_grad():
        preds = out["logits"].argmax(dim=-1)
        correct = int((preds == labels).sum().item())
        total = int(len(labels))

    return float(loss.item()) * accum_steps, correct, total


@torch.no_grad()
def _eval_epoch(model, loader, device, class_weights, class_names: Optional[List[str]] = None) -> Dict[str, float]:
    from ser.evaluation.runner import evaluate_split
    metrics, _, _, _, _, _ = evaluate_split(model, loader, device, class_weights, class_names=class_names)
    return metrics


def save_checkpoint(
    path: Path,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    cfg: Dict[str, Any],
    epoch: int,
    best_val_macro_f1: float,
    label_mapping: Dict[str, int] = EMOTION_TO_ID,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_key": cfg["model_key"],
            "display_name": cfg.get("display_name", cfg["model_key"]),
            "epoch": epoch,
            "best_val_macro_f1": best_val_macro_f1,
            "label_mapping": label_mapping,
            "config": cfg,
        },
        path / "model.pt",
    )
    torch.save(optimizer.state_dict(), path / "optimizer.pt")
    if scheduler is not None:
        torch.save(scheduler.state_dict(), path / "scheduler.pt")
    (path / "label_mapping.json").write_text(
        json.dumps(label_mapping, indent=2), encoding="utf-8"
    )
    (path / "training_state.json").write_text(
        json.dumps({"epoch": epoch, "best_val_macro_f1": best_val_macro_f1}),
        encoding="utf-8",
    )


def load_checkpoint_model(path: Path, model: torch.nn.Module) -> Dict[str, Any]:
    ckpt = torch.load(path / "model.pt", map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    return ckpt


def train_model(cfg: Dict[str, Any]) -> Dict[str, Any]:
    set_seed(int(cfg.get("seed", 42)))
    device = _get_device()
    paths = create_experiment_dirs(cfg["output_dir"])
    save_config(cfg, paths["config"])

    data_dir = cfg.get("data_dir")
    bundle = load_ravdess_splits(data_dir)
    assert_no_actor_leakage(bundle)

    labels_file = bundle.data_dir / "metadata" / "labels.json"
    if labels_file.exists():
        label_mapping = json.loads(labels_file.read_text(encoding="utf-8"))
    else:
        label_mapping = EMOTION_TO_ID
    cfg["num_classes"] = len(label_mapping)
    id_to_emotion = {int(v): k for k, v in label_mapping.items()}
    class_names = [id_to_emotion[i] for i in range(len(label_mapping))]

    display_name = cfg.get("display_name") or HUB_IDS.get(cfg["model_key"], {}).get(
        "display_name", cfg["model_key"]
    )
    cfg["display_name"] = display_name

    model = build_model(cfg).to(device)

    pretrained_ckpt = cfg.get("pretrained_checkpoint")
    if pretrained_ckpt and Path(pretrained_ckpt).exists():
        logger.info("Loading pretrained checkpoint for transfer learning from %s", pretrained_ckpt)
        ckpt_obj = torch.load(pretrained_ckpt, map_location=device)
        ckpt_state = ckpt_obj.get("model_state_dict", ckpt_obj) if isinstance(ckpt_obj, dict) else ckpt_obj
        model_state = model.state_dict()
        transferred = 0
        for k, v in ckpt_state.items():
            if k in model_state and model_state[k].shape == v.shape:
                model_state[k] = v
                transferred += 1
            elif k.startswith("encoder.") and k in model_state:
                if model_state[k].shape == v.shape:
                    model_state[k] = v
                    transferred += 1

        # Cross-corpus emotion head mapping
        source_mapping = None
        if isinstance(ckpt_obj, dict) and "label_mapping" in ckpt_obj:
            source_mapping = ckpt_obj["label_mapping"]
        else:
            source_label_json = Path(pretrained_ckpt).parent / "label_mapping.json"
            if source_label_json.exists():
                try:
                    source_mapping = json.loads(source_label_json.read_text(encoding="utf-8"))
                except Exception:
                    pass

        if source_mapping and "classifier.weight" in ckpt_state and "classifier.weight" in model_state:
            source_w = ckpt_state["classifier.weight"]
            source_b = ckpt_state.get("classifier.bias")
            canonical_map = {
                "neutral": "neutral",
                "happy": "happy",
                "happiness": "happy",
                "sad": "sad",
                "sadness": "sad",
                "angry": "angry",
                "anger": "angry",
                "fear": "fear",
                "fearful": "fear",
                "disgust": "disgust",
                "surprise": "surprise",
                "surprised": "surprise",
                "ps": "surprise",
                "calm": "neutral",
            }
            mapped_pairs = []
            unmapped_indices = []
            for target_name, target_idx in label_mapping.items():
                t_canon = canonical_map.get(str(target_name).lower(), str(target_name).lower())
                matched_source_idx = None
                matched_source_name = None
                for s_name, s_idx in source_mapping.items():
                    if canonical_map.get(str(s_name).lower(), str(s_name).lower()) == t_canon:
                        matched_source_idx = int(s_idx)
                        matched_source_name = str(s_name)
                        break
                if matched_source_idx is not None and matched_source_idx < source_w.size(0):
                    model_state["classifier.weight"][int(target_idx)] = source_w[matched_source_idx]
                    if source_b is not None and "classifier.bias" in model_state:
                        model_state["classifier.bias"][int(target_idx)] = source_b[matched_source_idx]
                    mapped_pairs.append(f"{matched_source_name}->{target_name}")
                else:
                    unmapped_indices.append(int(target_idx))

            if mapped_pairs and unmapped_indices:
                mean_w = source_w.mean(dim=0)
                mean_b = source_b.mean(dim=0) if source_b is not None else None
                for u_idx in unmapped_indices:
                    model_state["classifier.weight"][u_idx] = mean_w
                    if mean_b is not None and "classifier.bias" in model_state:
                        model_state["classifier.bias"][u_idx] = mean_b

            logger.info("Transferred classifier heads: %s (unmapped filled: %d)", mapped_pairs, len(unmapped_indices))

        model.load_state_dict(model_state)
        logger.info("Successfully transferred %d weights from pretrained checkpoint.", transferred)

    collator = build_collator(cfg)
    class_weights = None
    if cfg.get("class_weights", True):
        class_weights = compute_class_weights(bundle.train, num_classes=cfg["num_classes"])

    batch_size = int(cfg.get("batch_size", 4))
    train_loader = DataLoader(
        RAVDESSSERDataset(bundle.train, "train"),
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collator,
        num_workers=0,
    )
    val_loader = DataLoader(
        RAVDESSSERDataset(bundle.validation, "validation"),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collator,
        num_workers=0,
    )

    optimizer = torch.optim.AdamW(_param_groups(model, cfg))
    num_epochs = int(cfg.get("num_epochs", 20))
    warmup_ratio = float(cfg.get("warmup_ratio", 0.1))
    total_steps = max(1, len(train_loader) * num_epochs)
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lambda step: min(1.0, step / max(1, warmup_steps))
        if step < warmup_steps
        else max(0.0, (total_steps - step) / max(1, total_steps - warmup_steps)),
    )

    accum = int(cfg.get("gradient_accumulation_steps", 1))
    max_grad_norm = float(cfg.get("max_grad_norm", 1.0))
    use_amp = bool(cfg.get("mixed_precision", True)) and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler() if use_amp else None

    patience = int(cfg.get("early_stopping_patience", 5))
    best_val_f1 = -1.0
    best_epoch = 0
    stale = 0
    history: List[Dict] = []

    counts = model.count_parameters()
    hub_id = cfg.get("hub_id", "N/A")
    info_lines = [
        f"Model: {display_name}",
        f"Model key: {cfg['model_key']}",
        f"Hub ID: {hub_id}",
        f"Input type: {cfg.get('input_type', 'waveform')}",
        f"Hidden size: {counts.get('hidden_size', 'N/A')}",
        f"Total params: {counts['total']:,}",
        f"Trainable params: {counts['trainable']:,}",
        f"Batch size: {batch_size}",
        f"Accum steps: {accum}",
        f"Effective batch size: {batch_size * accum}",
        f"Num epochs: {num_epochs}",
        f"Patience: {patience}",
        f"Warmup ratio: {warmup_ratio}",
        f"Device: {device}",
        f"Mixed precision: {use_amp}",
        f"Num classes: {cfg['num_classes']}",
        f"Classes: {', '.join(class_names)}",
    ]
    info_text = "\n".join(info_lines)
    logger.info("Configuration summary:\n%s", info_text)
    paths["metrics"].mkdir(parents=True, exist_ok=True)
    (paths["metrics"] / "model_summary.txt").write_text(info_text, encoding="utf-8")

    train_start = time.time()
    global_step = 0

    for epoch in range(1, num_epochs + 1):
        model.train()
        epoch_loss = 0.0
        train_correct = 0
        train_total = 0
        optimizer.zero_grad(set_to_none=True)
        epoch_start = time.time()

        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch}", leave=False)):
            loss_val, corr, tot = _train_step(model, batch, device, class_weights, scaler, accum)
            epoch_loss += loss_val
            train_correct += corr
            train_total += tot

            if (step + 1) % accum == 0 or (step + 1) == len(train_loader):
                if use_amp:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()
                global_step += 1

        train_acc = train_correct / max(1, train_total)
        val_metrics = _eval_epoch(model, val_loader, device, class_weights, class_names=class_names)
        epoch_time = time.time() - epoch_start

        row = {
            "epoch": epoch,
            "train_loss": epoch_loss / max(1, len(train_loader)),
            "train_accuracy": train_acc,
            "train_macro_f1": 0.0,
            "val_loss": val_metrics.get("loss", 0.0),
            "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_weighted_f1": val_metrics["weighted_f1"],
            "val_uar": val_metrics["uar"],
            "val_war": val_metrics["war"],
            "epoch_time_sec": epoch_time,
        }
        history.append(row)
        logger.info(
            "epoch %d | train_acc=%.4f val_acc=%.4f val_f1=%.4f (%.1fs)",
            epoch, train_acc, val_metrics["accuracy"], val_metrics["macro_f1"], epoch_time,
        )

        if val_metrics["macro_f1"] > best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            best_epoch = epoch
            stale = 0
            save_checkpoint(
                paths["best_model"], model, optimizer, scheduler, cfg, epoch, best_val_f1, label_mapping=label_mapping
            )
        else:
            stale += 1

        if stale >= patience:
            logger.info("Early stopping at epoch %d", epoch)
            break

    save_checkpoint(
        paths["final_model"], model, optimizer, scheduler, cfg, epoch, best_val_f1, label_mapping=label_mapping
    )
    training_time = time.time() - train_start

    hist_df = pd.DataFrame(history)
    hist_path = paths["metrics"] / "training_history.csv"
    hist_df.to_csv(hist_path, index=False)
    plot_training_curves(hist_path, paths["metrics"])

    load_checkpoint_model(paths["best_model"], model)
    model.to(device)

    splits_loaders = {
        "train": DataLoader(RAVDESSSERDataset(bundle.train, "train"), batch_size=batch_size, collate_fn=collator),
        "validation": val_loader,
        "test": DataLoader(RAVDESSSERDataset(bundle.test, "test"), batch_size=batch_size, collate_fn=collator),
    }

    split_metrics = {}
    infer_start = time.time()
    for split_name, loader in splits_loaders.items():
        m, report, yt, yp, conf, meta = evaluate_split(model, loader, device, class_weights, class_names=class_names)
        save_split_results(
            paths["root"], split_name, m, report, yt, yp, conf, meta, display_name,
            class_names=class_names, id_to_emotion=id_to_emotion,
        )
        split_metrics[split_name] = m

    infer_time = time.time() - infer_start
    test_m = split_metrics["test"]

    final = {
        "model": display_name,
        "model_key": cfg["model_key"],
        "accuracy": test_m["accuracy"],
        "macro_precision": test_m["macro_precision"],
        "macro_recall": test_m["macro_recall"],
        "macro_f1": test_m["macro_f1"],
        "weighted_precision": test_m["weighted_precision"],
        "weighted_recall": test_m["weighted_recall"],
        "weighted_f1": test_m["weighted_f1"],
        "uar": test_m["uar"],
        "war": test_m["war"],
        "parameters": counts["total"],
        "trainable_parameters": counts["trainable"],
        "training_time_sec": training_time,
        "inference_time_sec": infer_time,
        "best_epoch": best_epoch,
        "best_val_macro_f1": best_val_f1,
    }
    pd.DataFrame([final]).to_csv(paths["metrics"] / "final_results.csv", index=False)
    pd.DataFrame(
        [{
            "total_training_time_sec": training_time,
            "avg_epoch_time_sec": training_time / max(1, len(history)),
            "total_inference_time_sec": infer_time,
            "avg_inference_per_file_sec": infer_time / max(1, len(bundle.test)),
        }]
    ).to_csv(paths["metrics"] / "computational_metrics.csv", index=False)

    info_lines = [
        f"Model: {cfg.get('display_name', cfg.get('model_key', 'SERModel'))}",
        f"Model key: {cfg.get('model_key')}",
        f"Hub ID: {cfg.get('hub_id', 'N/A')}",
        f"Input type: {cfg.get('input_type', 'waveform')}",
        f"Num classes: {cfg.get('num_classes')}",
        f"Parameters total: {counts['total']:,}",
        f"Parameters trainable: {counts['trainable']:,}",
        f"Parameters frozen: {counts['frozen']:,}",
        f"Device: {device.type}",
        f"Batch size: {batch_size}",
        f"Effective batch: {batch_size * accum}",
        f"Learning rate: {cfg.get('learning_rate', cfg.get('encoder_learning_rate', 'N/A'))}",
        f"Dropout: {cfg.get('dropout', 0.3)}",
        f"Class weights: {bool(class_weights is not None)}",
        f"Freeze encoder: {bool(cfg.get('freeze_encoder', False))}",
    ]
    (paths["metrics"] / "model_info.txt").write_text("\n".join(info_lines) + "\n", encoding="utf-8")

    logger.info("Training complete | test macro_f1=%.4f | output=%s", test_m["macro_f1"], paths["root"])
    del model
    del train_loader
    del val_loader
    if "splits_loaders" in locals():
        del splits_loaders
    import gc
    gc.collect()
    if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()
    return final
