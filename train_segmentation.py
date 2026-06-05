"""
train_segmentation.py
=====================
Trains a custom YOLOv8 instance segmentation model using the curated
masks_human dataset. Saves the best weights for deployment in predict_segmentation.py.

Usage:
    python train_segmentation.py
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATASET_YAML = os.path.join(PROJECT_ROOT, "dataset.yaml")
RUNS_DIR     = os.path.join(PROJECT_ROOT, "runs")

# ─── Training Config ──────────────────────────────────────────────────────────
CONFIG = {
    "model":      "yolov8n-seg.pt",   # Nano segmentation model (fast & accurate)
    "data":       DATASET_YAML,
    "epochs":     30,
    "imgsz":      640,
    "batch":      8,
    "lr0":        0.001,
    "optimizer":  "AdamW",
    "patience":   10,                  # Early stopping patience
    "project":    RUNS_DIR,
    "name":       "damage_seg",
    "exist_ok":   True,
    "save":       True,
    "cache":      False,               # Set True if you have >16GB RAM
    "device":     "",                  # Auto-detect GPU; falls back to CPU
    "workers":    2,
    "plots":      True,
    "verbose":    True,
}

def train():
    print("=" * 60)
    print("  Vehicle Damage Segmentation — YOLOv8 Training Pipeline")
    print("=" * 60)

    # Verify dataset exists
    if not os.path.exists(DATASET_YAML):
        print(f"\n[Error] dataset.yaml not found at: {DATASET_YAML}")
        print("Please run `python prepare_dataset.py` first to generate the dataset.\n")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("\n[Error] ultralytics package not installed.")
        print("Run: pip install ultralytics\n")
        sys.exit(1)

    print(f"\n[Train] Loading base model: {CONFIG['model']}")
    model = YOLO(CONFIG["model"])

    print(f"[Train] Starting training with config:")
    for k, v in CONFIG.items():
        print(f"  {k}: {v}")

    print(f"\n[Train] Training... (this may take 10–30 minutes on CPU)\n")

    results = model.train(
        data      = CONFIG["data"],
        epochs    = CONFIG["epochs"],
        imgsz     = CONFIG["imgsz"],
        batch     = CONFIG["batch"],
        lr0       = CONFIG["lr0"],
        optimizer = CONFIG["optimizer"],
        patience  = CONFIG["patience"],
        project   = CONFIG["project"],
        name      = CONFIG["name"],
        exist_ok  = CONFIG["exist_ok"],
        save      = CONFIG["save"],
        cache     = CONFIG["cache"],
        device    = CONFIG["device"],
        workers   = CONFIG["workers"],
        plots     = CONFIG["plots"],
        verbose   = CONFIG["verbose"],
    )

    best_pt = os.path.join(RUNS_DIR, CONFIG["name"], "weights", "best.pt")
    if os.path.exists(best_pt):
        import shutil
        dest = os.path.join(PROJECT_ROOT, "best.pt")
        shutil.copy2(best_pt, dest)
        print(f"\n[Train] Best model weights saved to: {dest}")
    else:
        print(f"\n[Train] Training done. Best weights located at: {best_pt}")

    print("\n[Train] === Training Complete ===")
    return results


if __name__ == "__main__":
    train()
