"""
XLSRTrainer — Training, Evaluation, Early Stopping, Checkpointing, and Artifact Logging.

Sections 10–23, 30–34.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import get_linear_schedule_with_warmup

from xlsr.constants import MODEL_NAME, NUM_CLASSES, SAMPLE_RATE
from xlsr.dataset import RAVDESSXLSRDataset, SERDataCollator
from xlsr.experiment_dirs import create_experiment_dirs
from xlsr.labels import CLASS_NAMES, EMOTION_TO_ID, ID_TO_EMOTION
from xlsr.metrics import compute_ser_metrics, plot_training_curves
from xlsr.model import Wav2Vec2XLSRForSER, build_xlsr_ser_model
from xlsr.processor import get_xlsr_processor

logger = logging.getLogger(__name__)


def get_device() -> torch.device:
    """Detect CUDA if available, otherwise return CPU device (Section 16)."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info("Using GPU: %s (%.2f GB VRAM)", gpu_name, gpu_mem)
        print(f"Device: cuda | GPU: {gpu_name} | VRAM: {gpu_mem:.2f} GB")
    else:
        device = torch.device("cpu")
        logger.info("CUDA unavailable. Running on CPU.")
        print("Device: cpu | CUDA unavailable")
    return device


class XLSRTrainer:
    """Trainer executing fine-tuning, validation, early stopping, and metric logging."""

    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: Union[Path, str],
        device: Optional[torch.device] = None,
    ) -> None:
        self.config = config
        self.dirs = create_experiment_dirs(output_dir)
        self.device = device or get_device()

        # Extract config parameters
        self.freeze_encoder = bool(config.get("freeze_encoder", False))
        self.batch_size = int(config.get("batch_size", 4))
        self.epochs = int(config.get("num_epochs", 20))
        self.encoder_lr = float(config.get("encoder_learning_rate", 1e-5))
        self.classifier_lr = float(config.get("classifier_learning_rate", 1e-4))
        self.weight_decay = float(config.get("weight_decay", 0.01))
        self.warmup_ratio = float(config.get("warmup_ratio", 0.1))
        self.grad_accum = int(config.get("gradient_accumulation_steps", 4))
        self.mixed_precision = bool(config.get("mixed_precision", True)) and self.device.type == "cuda"
        self.patience = int(config.get("early_stopping_patience", 5))

    def setup_model_and_processor(self) -> Tuple[Wav2Vec2XLSRForSER, SERDataCollator]:
        """Build model and data collator."""
        processor = get_xlsr_processor(model_name=MODEL_NAME)
        collator = SERDataCollator(processor)

        model = build_xlsr_ser_model(
            model_name=MODEL_NAME,
            num_classes=NUM_CLASSES,
            dropout=float(self.config.get("dropout", 0.3)),
            freeze_encoder=self.freeze_encoder,
        )
        model.to(self.device)
        return model, collator

    def create_optimizer_and_scheduler(
        self,
        model: Wav2Vec2XLSRForSER,
        num_training_steps: int,
    ) -> Tuple[torch.optim.Optimizer, Any]:
        """Configure AdamW with differential learning rates (Section 11, 20)."""
        if self.freeze_encoder:
            params = [
                {"params": model.classifier.parameters(), "lr": self.classifier_lr, "weight_decay": self.weight_decay}
            ]
        else:
            params = [
                {"params": model.encoder.parameters(), "lr": self.encoder_lr, "weight_decay": self.weight_decay},
                {"params": model.classifier.parameters(), "lr": self.classifier_lr, "weight_decay": self.weight_decay},
            ]

        optimizer = torch.optim.AdamW(params)
        num_warmup_steps = int(num_training_steps * self.warmup_ratio)

        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=num_training_steps,
        )
        return optimizer, scheduler

    def save_checkpoint(
        self,
        model: Wav2Vec2XLSRForSER,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        epoch: int,
        best_val_macro_f1: float,
        checkpoint_dir: Path,
    ) -> Path:
        """Save complete model checkpoint (Section 22)."""
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
            "epoch": epoch,
            "best_val_macro_f1": best_val_macro_f1,
            "config": self.config,
            "label_mapping": {"EMOTION_TO_ID": EMOTION_TO_ID, "ID_TO_EMOTION": ID_TO_EMOTION},
        }
        torch.save(state, checkpoint_dir / "model_checkpoint.pt")

        # Also save model config/weights cleanly
        model.encoder.save_pretrained(checkpoint_dir)
        torch.save(model.classifier.state_dict(), checkpoint_dir / "classifier_head.pt")

        logger.info("Saved checkpoint to %s | Val Macro-F1: %.4f", checkpoint_dir, best_val_macro_f1)
        return checkpoint_dir

    def log_model_info(self, model: Wav2Vec2XLSRForSER, output_dir: Path) -> Path:
        """Save model summary to metrics/model_info.txt (Section 30)."""
        counts = model.count_parameters()
        eff_batch = self.batch_size * self.grad_accum
        lines = [
            "Wav2Vec2-XLS-R-300M SER Model Summary",
            "=" * 45,
            f"Model name: {MODEL_NAME}",
            f"Total parameters: {counts['total']:,}",
            f"Trainable parameters: {counts['trainable']:,}",
            f"Frozen parameters: {counts['total'] - counts['trainable']:,}",
            f"Encoder parameters: {counts['encoder']:,}",
            f"Classifier parameters: {counts['classifier']:,}",
            f"Number of classes: {NUM_CLASSES}",
            f"Input sampling rate: {SAMPLE_RATE} Hz",
            f"Batch size: {self.batch_size}",
            f"Gradient accumulation steps: {self.grad_accum}",
            f"Effective batch size: {eff_batch}",
            f"Encoder learning rate: {self.encoder_lr}",
            f"Classifier learning rate: {self.classifier_lr}",
            f"Freeze encoder: {self.freeze_encoder}",
            f"Device: {self.device}",
        ]
        info_path = output_dir / "metrics" / "model_info.txt"
        info_path.parent.mkdir(parents=True, exist_ok=True)
        info_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("Saved model info to %s", info_path)
        return info_path

    def train_epoch(
        self,
        model: Wav2Vec2XLSRForSER,
        dataloader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        scaler: Optional[torch.cuda.amp.GradScaler] = None,
        epoch: int = 1,
        total_epochs: int = 1,
    ) -> Tuple[float, float, float]:
        """Train model for one epoch with gradient accumulation, clipping, and progress bar."""
        model.train()
        total_loss = 0.0
        all_preds = []
        all_labels = []

        optimizer.zero_grad()
        pbar = tqdm(
            dataloader,
            desc=f"Epoch {epoch:02d}/{total_epochs:02d} [Train]",
            leave=False,
            dynamic_ncols=True,
        )

        for step, batch in enumerate(pbar):
            input_values = batch["input_values"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)

            if self.mixed_precision and scaler is not None:
                with torch.amp.autocast("cuda"):
                    outputs = model(input_values=input_values, attention_mask=attention_mask, labels=labels)
                    loss = outputs.loss / self.grad_accum
                scaler.scale(loss).backward()
            else:
                outputs = model(input_values=input_values, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss / self.grad_accum
                loss.backward()

            batch_loss = loss.item() * self.grad_accum
            total_loss += batch_loss
            preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

            pbar.set_postfix({"loss": f"{batch_loss:.4f}"})

            if (step + 1) % self.grad_accum == 0 or (step + 1) == len(dataloader):
                if self.mixed_precision and scaler is not None:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    scale_before = scaler.get_scale()
                    scaler.step(optimizer)
                    scaler.update()
                    scale_after = scaler.get_scale()
                    if scale_before <= scale_after:
                        scheduler.step()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    scheduler.step()

                optimizer.zero_grad()

        avg_loss = total_loss / len(dataloader)
        metrics = compute_ser_metrics(all_labels, all_preds)
        return avg_loss, metrics["accuracy"], metrics["macro_f1"]

    def evaluate(
        self,
        model: Wav2Vec2XLSRForSER,
        dataloader: DataLoader,
        desc: str = "[Val]",
    ) -> Tuple[float, Dict[str, float], np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate model on validation or test set with progress bar."""
        model.eval()
        total_loss = 0.0
        all_preds = []
        all_labels = []
        all_probs = []

        pbar = tqdm(dataloader, desc=desc, leave=False, dynamic_ncols=True)
        with torch.no_grad():
            for batch in pbar:
                input_values = batch["input_values"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = model(input_values=input_values, attention_mask=attention_mask, labels=labels)
                loss_val = outputs.loss.item()
                total_loss += loss_val
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
                preds = np.argmax(probs, axis=-1)

                all_preds.extend(preds)
                all_labels.extend(labels.cpu().numpy())
                all_probs.extend(probs)

                pbar.set_postfix({"val_loss": f"{loss_val:.4f}"})

        avg_loss = total_loss / len(dataloader)
        metrics = compute_ser_metrics(all_labels, all_preds)
        return avg_loss, metrics, np.array(all_labels), np.array(all_preds), np.array(all_probs)

    def run_training(
        self,
        train_dataset: RAVDESSXLSRDataset,
        val_dataset: RAVDESSXLSRDataset,
    ) -> Dict[str, Any]:
        """Full training loop with validation, early stopping, and plot generation."""
        model, collator = self.setup_model_and_processor()
        self.log_model_info(model, self.dirs["root"])

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=collator,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=collator,
        )

        num_update_steps_per_epoch = len(train_loader) // self.grad_accum
        total_training_steps = num_update_steps_per_epoch * self.epochs
        optimizer, scheduler = self.create_optimizer_and_scheduler(model, total_training_steps)

        scaler = torch.amp.GradScaler("cuda") if self.mixed_precision else None

        best_val_macro_f1 = -1.0
        patience_counter = 0
        history = []
        epoch_times = []

        logger.info("Starting training | Epochs: %d | Batch size: %d", self.epochs, self.batch_size)
        start_train_time = time.time()

        for epoch in range(1, self.epochs + 1):
            epoch_start = time.time()
            train_loss, train_acc, train_f1 = self.train_epoch(
                model, train_loader, optimizer, scheduler, scaler, epoch=epoch, total_epochs=self.epochs
            )
            val_loss, val_metrics, _, _, _ = self.evaluate(
                model, val_loader, desc=f"Epoch {epoch:02d}/{self.epochs:02d} [Val]"
            )
            epoch_duration = time.time() - epoch_start
            epoch_times.append(epoch_duration)

            history.append({
                "epoch": epoch,
                "train_loss": train_loss,
                "train_accuracy": train_acc,
                "train_macro_f1": train_f1,
                "val_loss": val_loss,
                "val_accuracy": val_metrics["accuracy"],
                "val_macro_f1": val_metrics["macro_f1"],
                "val_weighted_f1": val_metrics["weighted_f1"],
                "val_uar": val_metrics["uar"],
                "val_war": val_metrics["war"],
            })

            log_msg = (
                f"Epoch {epoch:02d}/{self.epochs:02d} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}% | "
                f"Val Loss: {val_loss:.4f} | Val Acc (WAR): {val_metrics['accuracy']*100:.2f}% | "
                f"Val UAR: {val_metrics['uar']*100:.2f}% | Val Macro-F1: {val_metrics['macro_f1']:.4f} | "
                f"Time: {epoch_duration:.1f}s"
            )
            logger.info(log_msg)
            print(log_msg)

            # Early stopping check on Validation Macro-F1 (Section 21)
            if val_metrics["macro_f1"] > best_val_macro_f1:
                best_val_macro_f1 = val_metrics["macro_f1"]
                patience_counter = 0
                self.save_checkpoint(
                    model, optimizer, scheduler, epoch, best_val_macro_f1, self.dirs["best_model"]
                )
            else:
                patience_counter += 1
                if patience_counter >= self.patience:
                    logger.info("Early stopping triggered at epoch %d", epoch)
                    print(f"Early stopping triggered at epoch {epoch}")
                    break

        total_training_time = time.time() - start_train_time
        avg_epoch_time = float(np.mean(epoch_times)) if epoch_times else 0.0

        # Save final model checkpoint
        self.save_checkpoint(
            model, optimizer, scheduler, len(history), best_val_macro_f1, self.dirs["final_model"]
        )

        # Save training history CSV
        history_df = pd.DataFrame(history)
        history_path = self.dirs["metrics"] / "training_history.csv"
        history_df.to_csv(history_path, index=False)
        plot_training_curves(history_df, self.dirs["root"])

        return {
            "best_val_macro_f1": best_val_macro_f1,
            "total_training_time": total_training_time,
            "avg_epoch_time": avg_epoch_time,
            "history_df": history_df,
        }
