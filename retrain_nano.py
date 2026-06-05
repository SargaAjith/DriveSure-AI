"""
retrain_nano.py
================
Retrain YOLOv8n-seg on the cleaned v2 dataset (with large whole-car false positive masks removed).
Trains for 15 epochs on CPU.
"""
import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATASET_YAML = os.path.join(PROJECT_ROOT, "dataset_v2.yaml")
RUNS_DIR     = os.path.join(PROJECT_ROOT, "runs")

def train():
    print("=" * 60)
    print("  YOLOv8n-seg Retraining on Cleaned v2 Dataset")
    print("=" * 60)

    if not os.path.exists(DATASET_YAML):
        print(f"ERROR: {DATASET_YAML} not found.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: pip install ultralytics")
        sys.exit(1)

    # Load best_backup_s.pt (YOLOv8s-seg) for fast fine-tuning
    model = YOLO("best_backup_s.pt")

    print(f"\nFine-tuning with best_backup_s.pt on cleaned v2 dataset (Fast CPU config)...")
    model.train(
        data      = DATASET_YAML,
        epochs    = 30,
        imgsz     = 320,
        batch     = 8,
        lr0       = 0.0005,
        optimizer = "AdamW",
        patience  = 10,
        project   = RUNS_DIR,
        name      = "damage_seg_s_v2_fast",
        exist_ok  = True,
        save      = True,
        cache     = False,
        device    = "cpu",
        workers   = 2,
        plots     = True,
        verbose   = True,
    )

    best_pt = os.path.join(RUNS_DIR, "damage_seg_s_v2_fast", "weights", "best.pt")
    if os.path.exists(best_pt):
        dest = os.path.join(PROJECT_ROOT, "best.pt")
        shutil.copy2(best_pt, dest)
        print(f"\n[Train] Best model saved to: {dest}")
    else:
        print("ERROR: best.pt weights not found after training.")

    print("\n[Train] === Training Complete ===")

if __name__ == "__main__":
    train()
