"""
Training pipeline for the universal compiler/translator/AI/GDT model.

Trains from scratch using synthetic data. No external APIs.
Supports:
- Encoder-decoder training (patching, completion, translation)
- Gap detection training (classification)
- Mixed-task training with weighted sampling
- Checkpointing and resumption
- Learning rate warmup + cosine decay

Usage:
    python -m aura.training.train
    python -m aura.training.train --config esp32_gap_model/config.yaml
"""

import os
import math
import time
import yaml
import torch
import torch.nn as nn
from typing import Dict, Optional
from pathlib import Path

from aura.core.model.architecture import GapDetectorModel
from aura.core.gdt.engine import GapDetectionHead, NUM_GAP_CATEGORIES
from aura.plugins.esp32.model import ESP32GapModel
from aura.core.data.generator import SyntheticDataGenerator
from aura.core.tokenizer.byte_tokenizer import ByteTokenizer


class Trainer:
    """
    Full training pipeline. Runs offline, no APIs.

    Trains both:
    1. PC model (encoder-decoder for patching/translation/completion)
    2. ESP32 model (tiny encoder-only for gap detection)
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        # Load config
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()

        # Device
        if device:
            self.device = torch.device(device)
        else:
            auto = self.config.get("training", {}).get("device", "auto")
            if auto == "auto":
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.device = torch.device(auto)

        self.tokenizer = ByteTokenizer()
        self.data_gen = SyntheticDataGenerator()

        # Build models
        pc_cfg = self.config.get("pc_model", {})
        self.pc_model = GapDetectorModel(
            vocab_size=pc_cfg.get("vocab_size", 512),
            dim=pc_cfg.get("dim", 512),
            encoder_layers=pc_cfg.get("encoder_layers", 8),
            decoder_layers=pc_cfg.get("decoder_layers", 8),
            heads=pc_cfg.get("heads", 8),
            ff_dim=pc_cfg.get("ff_dim", 2048),
            max_seq_len=pc_cfg.get("max_seq_len", 1024),
            dropout=pc_cfg.get("dropout", 0.1),
        ).to(self.device)

        # GDT head attaches to encoder
        self.gdt_head = GapDetectionHead(
            dim=pc_cfg.get("dim", 512),
            num_categories=NUM_GAP_CATEGORIES,
        ).to(self.device)

        esp_cfg = self.config.get("esp32_model", {})
        self.esp32_model = ESP32GapModel(
            vocab_size=esp_cfg.get("vocab_size", 512),
            dim=esp_cfg.get("dim", 64),
            layers=esp_cfg.get("encoder_layers", 2),
            heads=esp_cfg.get("heads", 4),
            ff_dim=esp_cfg.get("ff_dim", 256),
            max_seq_len=esp_cfg.get("max_seq_len", 256),
            num_gap_categories=NUM_GAP_CATEGORIES,
        ).to(self.device)

        print(f"PC model: {self.pc_model.count_parameters():,} parameters")
        print(f"GDT head: {sum(p.numel() for p in self.gdt_head.parameters()):,} parameters")
        print(f"ESP32 model: {self.esp32_model.count_parameters():,} parameters")
        print(f"ESP32 estimated size: {self.esp32_model.estimate_size_bytes(quantized=True):,} bytes (int8)")
        print(f"Device: {self.device}")

    def _default_config(self) -> Dict:
        return {
            "pc_model": {
                "vocab_size": 512, "dim": 512, "encoder_layers": 8,
                "decoder_layers": 8, "heads": 8, "ff_dim": 2048,
                "max_seq_len": 1024, "dropout": 0.1,
            },
            "esp32_model": {
                "vocab_size": 512, "dim": 64, "encoder_layers": 2,
                "decoder_layers": 2, "heads": 4, "ff_dim": 256,
                "max_seq_len": 256, "dropout": 0.0,
            },
            "training": {
                "batch_size": 32, "learning_rate": 3e-4,
                "warmup_steps": 1000, "max_steps": 50000,
                "grad_clip": 1.0, "weight_decay": 0.01,
                "checkpoint_every": 5000, "eval_every": 1000,
                "device": "auto",
            },
        }

    def _get_lr(self, step: int, warmup: int, max_steps: int, base_lr: float) -> float:
        """Warmup + cosine decay learning rate schedule."""
        if step < warmup:
            return base_lr * step / max(warmup, 1)
        progress = (step - warmup) / max(max_steps - warmup, 1)
        return base_lr * 0.5 * (1.0 + math.cos(math.pi * progress))

    def train_pc_model(
        self,
        max_steps: Optional[int] = None,
        checkpoint_dir: str = "checkpoints",
        resume_from: Optional[str] = None,
    ) -> None:
        """
        Train the PC (full-size) encoder-decoder model.

        Handles patching, completion, translation, and gap detection tasks.
        """
        t_cfg = self.config.get("training", {})
        max_steps = max_steps or t_cfg.get("max_steps", 50000)
        batch_size = t_cfg.get("batch_size", 32)
        base_lr = t_cfg.get("learning_rate", 3e-4)
        warmup = t_cfg.get("warmup_steps", 1000)
        grad_clip = t_cfg.get("grad_clip", 1.0)
        weight_decay = t_cfg.get("weight_decay", 0.01)
        checkpoint_every = t_cfg.get("checkpoint_every", 5000)
        eval_every = t_cfg.get("eval_every", 1000)
        max_seq_len = self.config.get("pc_model", {}).get("max_seq_len", 1024)

        os.makedirs(checkpoint_dir, exist_ok=True)

        # Optimizers
        pc_params = list(self.pc_model.parameters()) + list(self.gdt_head.parameters())
        optimizer = torch.optim.AdamW(pc_params, lr=base_lr, weight_decay=weight_decay)

        # Loss functions
        seq_loss_fn = nn.CrossEntropyLoss(ignore_index=0)  # ignore PAD
        gap_detect_loss_fn = nn.BCEWithLogitsLoss()
        gap_class_loss_fn = nn.CrossEntropyLoss(ignore_index=0)

        start_step = 0
        if resume_from and os.path.exists(resume_from):
            checkpoint = torch.load(resume_from, map_location=self.device)
            self.pc_model.load_state_dict(checkpoint["pc_model"])
            self.gdt_head.load_state_dict(checkpoint["gdt_head"])
            optimizer.load_state_dict(checkpoint["optimizer"])
            start_step = checkpoint.get("step", 0)
            print(f"Resumed from step {start_step}")

        self.pc_model.train()
        self.gdt_head.train()

        print(f"\n{'='*60}")
        print(f"Training PC model: {max_steps} steps, batch {batch_size}")
        print(f"{'='*60}\n")

        total_loss_accum = 0.0
        start_time = time.time()

        for step in range(start_step, max_steps):
            # Update learning rate
            lr = self._get_lr(step, warmup, max_steps, base_lr)
            for param_group in optimizer.param_groups:
                param_group["lr"] = lr

            # Generate batch
            batch = self.data_gen.generate_batch(
                batch_size=batch_size,
                max_seq_len=max_seq_len,
            )
            src = batch["src"].to(self.device)
            tgt = batch["tgt"].to(self.device)
            task_types = batch["task_types"]

            optimizer.zero_grad()
            total_loss = torch.tensor(0.0, device=self.device)

            # Separate batch by task type
            seq_indices = [i for i, t in enumerate(task_types) if t != "gap_detection"]
            gdt_indices = [i for i, t in enumerate(task_types) if t == "gap_detection"]

            # Sequence-to-sequence loss (patching, completion, translation)
            if seq_indices:
                seq_src = src[seq_indices]
                seq_tgt = tgt[seq_indices]
                # Teacher forcing: shift target right
                tgt_input = seq_tgt[:, :-1]
                tgt_expected = seq_tgt[:, 1:]

                logits = self.pc_model(seq_src, tgt_input)
                vocab_size = logits.size(-1)
                loss_seq = seq_loss_fn(
                    logits.reshape(-1, vocab_size),
                    tgt_expected.reshape(-1),
                )
                total_loss = total_loss + loss_seq

            # Gap detection loss
            if gdt_indices:
                gdt_src = src[gdt_indices]
                gdt_labels = tgt[gdt_indices].float()

                encoder_out = self.pc_model.encode(gdt_src)
                pad_mask = (gdt_src != 0)
                gdt_output = self.gdt_head(encoder_out, pad_mask)

                # Binary gap detection loss
                binary_labels = (gdt_labels > 0).float()
                loss_detect = gap_detect_loss_fn(
                    gdt_output["token_gap_probs"],
                    binary_labels,
                )

                # Category classification loss (only on gap tokens)
                gap_mask = gdt_labels > 0
                if gap_mask.any():
                    cat_logits = gdt_output["token_gap_categories"][gap_mask]
                    cat_targets = gdt_labels[gap_mask].long()
                    loss_class = gap_class_loss_fn(cat_logits, cat_targets)
                    total_loss = total_loss + loss_detect + loss_class * 0.5
                else:
                    total_loss = total_loss + loss_detect

            total_loss.backward()

            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(pc_params, grad_clip)

            optimizer.step()
            total_loss_accum += total_loss.item()

            # Logging
            if step % eval_every == 0 and step > 0:
                avg_loss = total_loss_accum / eval_every
                elapsed = time.time() - start_time
                steps_per_sec = step / max(elapsed, 1)
                eta = (max_steps - step) / max(steps_per_sec, 0.01)
                print(
                    f"step {step:>6d}/{max_steps} | "
                    f"loss {avg_loss:.4f} | "
                    f"lr {lr:.2e} | "
                    f"{steps_per_sec:.1f} steps/s | "
                    f"ETA {eta/60:.0f}min"
                )
                total_loss_accum = 0.0

            # Checkpoint
            if step % checkpoint_every == 0 and step > 0:
                ckpt_path = os.path.join(checkpoint_dir, f"pc_model_step{step}.pt")
                torch.save({
                    "step": step,
                    "pc_model": self.pc_model.state_dict(),
                    "gdt_head": self.gdt_head.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "config": self.config,
                }, ckpt_path)
                print(f"Checkpoint saved: {ckpt_path}")

        # Final save
        final_path = os.path.join(checkpoint_dir, "pc_model_final.pt")
        torch.save({
            "step": max_steps,
            "pc_model": self.pc_model.state_dict(),
            "gdt_head": self.gdt_head.state_dict(),
            "config": self.config,
        }, final_path)
        print(f"\nTraining complete. Final model: {final_path}")

    def train_esp32_model(
        self,
        max_steps: Optional[int] = None,
        checkpoint_dir: str = "checkpoints",
    ) -> None:
        """Train the tiny ESP32 gap detection model."""
        t_cfg = self.config.get("training", {})
        max_steps = max_steps or min(t_cfg.get("max_steps", 50000), 20000)
        batch_size = t_cfg.get("batch_size", 32)
        base_lr = t_cfg.get("learning_rate", 3e-4)
        max_seq_len = self.config.get("esp32_model", {}).get("max_seq_len", 256)

        os.makedirs(checkpoint_dir, exist_ok=True)

        optimizer = torch.optim.AdamW(self.esp32_model.parameters(), lr=base_lr)
        gap_detect_loss_fn = nn.BCEWithLogitsLoss()
        gap_class_loss_fn = nn.CrossEntropyLoss(ignore_index=0)

        self.esp32_model.train()

        print(f"\n{'='*60}")
        print(f"Training ESP32 model: {max_steps} steps")
        print(f"{'='*60}\n")

        for step in range(max_steps):
            batch = self.data_gen.generate_batch(
                batch_size=batch_size,
                max_seq_len=max_seq_len,
                task_weights={"gap_detection": 1.0, "patch": 0.0, "completion": 0.0, "translation": 0.0},
            )
            src = batch["src"].to(self.device)
            labels = batch["tgt"].to(self.device).float()

            optimizer.zero_grad()
            output = self.esp32_model(src)

            binary_labels = (labels > 0).float()
            loss = gap_detect_loss_fn(output["gap_probs"], binary_labels)

            gap_mask = labels > 0
            if gap_mask.any():
                cat_logits = output["gap_categories"][gap_mask]
                cat_targets = labels[gap_mask].long()
                loss = loss + gap_class_loss_fn(cat_logits, cat_targets) * 0.5

            loss.backward()
            optimizer.step()

            if step % 1000 == 0:
                print(f"[ESP32] step {step}/{max_steps} | loss {loss.item():.4f}")

        esp_path = os.path.join(checkpoint_dir, "esp32_model_final.pt")
        torch.save({
            "model": self.esp32_model.state_dict(),
            "config": self.config.get("esp32_model", {}),
        }, esp_path)
        print(f"ESP32 model saved: {esp_path}")

    def train_all(
        self,
        pc_steps: Optional[int] = None,
        esp_steps: Optional[int] = None,
        checkpoint_dir: str = "checkpoints",
    ) -> None:
        """Train both PC and ESP32 models."""
        self.train_pc_model(max_steps=pc_steps, checkpoint_dir=checkpoint_dir)
        self.train_esp32_model(max_steps=esp_steps, checkpoint_dir=checkpoint_dir)
        print("\nAll training complete!")


def main():
    """Entry point for training."""
    import argparse

    parser = argparse.ArgumentParser(description="Train the GapDetector model")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    parser.add_argument("--steps", type=int, default=None, help="Max training steps")
    parser.add_argument("--esp-steps", type=int, default=None, help="ESP32 model steps")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda/cpu)")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--resume", type=str, default=None, help="Resume from checkpoint")
    parser.add_argument("--pc-only", action="store_true", help="Only train PC model")
    parser.add_argument("--esp-only", action="store_true", help="Only train ESP32 model")
    args = parser.parse_args()

    trainer = Trainer(config_path=args.config, device=args.device)

    if args.esp_only:
        trainer.train_esp32_model(max_steps=args.esp_steps, checkpoint_dir=args.checkpoint_dir)
    elif args.pc_only:
        trainer.train_pc_model(
            max_steps=args.steps,
            checkpoint_dir=args.checkpoint_dir,
            resume_from=args.resume,
        )
    else:
        trainer.train_all(
            pc_steps=args.steps,
            esp_steps=args.esp_steps,
            checkpoint_dir=args.checkpoint_dir,
        )


if __name__ == "__main__":
    main()
