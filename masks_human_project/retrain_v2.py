"""
Retrain YOLOv8s-seg on the improved v2 dataset with tighter masks.
"""
import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATASET_YAML = os.path.join(PROJECT_ROOT, "dataset_v2.yaml")
RUNS_DIR     = os.path.join(PROJECT_ROOT, "runs")

def train():
    print("=" * 60)
    print("  YOLOv8s-seg Retraining on v2 Dataset (Tighter Masks)")
    print("=" * 60)

    if not os.path.exists(DATASET_YAML):
        print(f"ERROR: {DATASET_YAML} not found. Run prepare_dataset_v2.py first.")
        sys.exit(1)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: pip install ultralytics")
        sys.exit(1)

    # Use yolov8s-seg (small) for better accuracy than nano
    model = YOLO("yolov8s-seg.pt")

    print(f"\nTraining with yolov8s-seg on v2 dataset...")
    model.train(
        data      = DATASET_YAML,
        epochs    = 50,
        imgsz     = 640,
        batch     = 8,
        lr0       = 0.001,
        optimizer = "AdamW",
        patience  = 15,
        project   = RUNS_DIR,
        name      = "damage_seg_v2",
        exist_ok  = True,
        save      = True,
        cache     = False,
        device    = "",
        workers   = 2,
        plots     = True,
        verbose   = True,
        # Augmentation for better generalization
        hsv_h     = 0.015,
        hsv_s     = 0.5,
        hsv_v     = 0.3,
        degrees   = 10.0,
        translate = 0.1,
        scale     = 0.4,
        flipud    = 0.0,
        fliplr    = 0.5,
        mosaic    = 0.8,
    )

    best_pt = os.path.join(RUNS_DIR, "damage_seg_v2", "weights", "best.pt")
    if os.path.exists(best_pt):
        dest = os.path.join(PROJECT_ROOT, "best.pt")
        shutil.copy2(best_pt, dest)
        print(f"\n[Train] Best model saved to: {dest}")

    print("\n[Train] === Training Complete ===")

if __name__ == "__main__":
    train()
