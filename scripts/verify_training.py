#!/usr/bin/env python3
"""Verify all 8 SER models are ready for training (config, data, model, batch, backward)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch
from torch.utils.data import DataLoader

from ser.core.config import load_model_config
from ser.core.paths import ALL_MODEL_KEYS, OUTPUTS_ROOT
from ser.core.registry import HUB_IDS, build_collator, build_model
from ser.data.class_weights import compute_class_weights
from ser.data.torch_dataset import RAVDESSSERDataset
from ser.training.experiment import create_experiment_dirs
from xlsr.data.dataset import load_ravdess_splits
from xlsr.data.split import assert_no_actor_leakage


def _check_model(key: str) -> tuple[bool, str]:
    cfg = load_model_config(key)
    model = build_model(cfg)
    collator = build_collator(cfg)

    bundle = load_ravdess_splits(cfg["data_dir"])
    assert_no_actor_leakage(bundle)

    batch_size = min(2, int(cfg.get("batch_size", 2)))
    loader = DataLoader(
        RAVDESSSERDataset(bundle.train.head(4), "train"),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collator,
        num_workers=0,
    )
    batch = next(iter(loader))
    class_weights = compute_class_weights(bundle.train) if cfg.get("class_weights", True) else None

    labels = batch["labels"]
    cw = class_weights
    mask = batch.get("attention_mask")
    if "input_values" in batch:
        inputs = {"input_values": batch["input_values"], "attention_mask": mask}
    else:
        inputs = {"mfcc": batch["mfcc"], "attention_mask": mask}

    out = model(**inputs, labels=labels, class_weights=cw)
    loss = out["loss"]
    if loss is None:
        return False, "loss is None"
    loss.backward()

    counts = model.count_parameters()
    logits = out["logits"]
    if logits.shape != (batch_size, 8):
        return False, f"logits shape {tuple(logits.shape)} != ({batch_size}, 8)"

    # Verify output dirs writable
    out_dir = cfg["output_dir"]
    paths = create_experiment_dirs(out_dir)
    if not paths["root"].exists():
        return False, f"cannot create output dir {out_dir}"

    hub = cfg.get("hub_id") or HUB_IDS.get(key, {}).get("hub_id", "-")
    note = ""
    if key == "emotion2vec_plus" and "wav2vec2-base" in str(hub):
        note = " [proxy: wav2vec2-base]"
    if key == "beats" and "wavlm" in str(hub).lower():
        note = " [proxy: wavlm]"

    return True, (
        f"params={counts['total']:,} | batch={batch_size} | "
        f"loss={float(loss.detach()):.4f} | hub={hub}{note}"
    )


def main() -> int:
    print("SER Training Readiness Check")
    print("=" * 72)

    # Dataset
    bundle = load_ravdess_splits()
    assert_no_actor_leakage(bundle)
    print(f"Dataset OK: train={len(bundle.train)} val={len(bundle.validation)} test={len(bundle.test)}")
    print(f"Device: {'cuda - ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")
    print()

    passed = 0
    failed = []
    for key in ALL_MODEL_KEYS:
        try:
            ok, msg = _check_model(key)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {key:<22} {msg}")
            if ok:
                passed += 1
            else:
                failed.append((key, msg))
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {key:<22} {exc}")
            failed.append((key, str(exc)))

    print()
    print(f"Result: {passed}/{len(ALL_MODEL_KEYS)} models ready for training")

    # Existing training outputs
    print()
    print("Existing training outputs:")
    for key in ALL_MODEL_KEYS:
        final = OUTPUTS_ROOT / key / "metrics" / "final_results.csv"
        best = OUTPUTS_ROOT / key / "checkpoints" / "best_model" / "model.pt"
        if final.exists() and best.exists():
            print(f"  {key:<22} trained (checkpoint exists)")
        elif best.exists():
            print(f"  {key:<22} partial (checkpoint only)")
        else:
            print(f"  {key:<22} not trained yet")

    report_path = OUTPUTS_ROOT / "comparison" / "training_readiness.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"Passed: {passed}/{len(ALL_MODEL_KEYS)}"]
    for key, msg in failed:
        lines.append(f"FAIL {key}: {msg}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSaved: {report_path}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
