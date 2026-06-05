"""
download_and_train.py
=====================
Downloads a professional car damage detection dataset from Roboflow Universe
and trains YOLOv8 on it for accurate damage detection.

Dataset: Car Damage Detection with classes: dent, scratch, crack, broken, damage
"""

import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def download_dataset():
    """Download professional car damage dataset from Roboflow."""
    print("=" * 60)
    print("  Downloading Professional Car Damage Dataset")
    print("=" * 60)

    try:
        from roboflow import Roboflow
    except ImportError:
        print("ERROR: pip install roboflow")
        sys.exit(1)

    # Roboflow public dataset - no API key needed for public datasets
    # Using a well-annotated car damage detection dataset
    rf = Roboflow(api_key="BpYEFsx3DqHOlaBOwOMI")  # Public demo key
    
    # Try multiple good car damage datasets
    datasets_to_try = [
        ("university-bswcg", "car-damage-detection-sxzx5", 4),
        ("car-damage-detection-trqfq", "car-damage-detection-trqfq", 1),
    ]
    
    dataset = None
    for workspace, project_name, version_num in datasets_to_try:
        try:
            print(f"\nTrying: {workspace}/{project_name} v{version_num}")
            project = rf.workspace(workspace).project(project_name)
            dataset_path = os.path.join(PROJECT_ROOT, "roboflow_dataset")
            dataset = project.version(version_num).download(
                "yolov8",
                location=dataset_path
            )
            print(f"✅ Downloaded to: {dataset_path}")
            return dataset_path
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue
    
    if dataset is None:
        print("\nFalling back to manual dataset preparation...")
        return None


def train_model(dataset_path):
    """Train YOLOv8 on the professional dataset."""
    print("\n" + "=" * 60)
    print("  Training YOLOv8s-seg on Professional Dataset")
    print("=" * 60)

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: pip install ultralytics")
        sys.exit(1)

    # Find data.yaml
    yaml_path = os.path.join(dataset_path, "data.yaml")
    if not os.path.exists(yaml_path):
        # Search subdirectories
        for root, dirs, files in os.walk(dataset_path):
            if "data.yaml" in files:
                yaml_path = os.path.join(root, "data.yaml")
                break

    if not os.path.exists(yaml_path):
        print(f"ERROR: data.yaml not found in {dataset_path}")
        sys.exit(1)

    print(f"\nDataset config: {yaml_path}")
    with open(yaml_path) as f:
        print(f.read())

    # Use YOLOv8s (small) for good balance of speed and accuracy
    model = YOLO("yolov8s.pt")

    print("\nStarting training...")
    results = model.train(
        data      = yaml_path,
        epochs    = 50,
        imgsz     = 640,
        batch     = 8,
        lr0       = 0.001,
        optimizer = "AdamW",
        patience  = 15,
        project   = os.path.join(PROJECT_ROOT, "runs"),
        name      = "damage_pro",
        exist_ok  = True,
        save      = True,
        device    = "",
        workers   = 2,
        plots     = True,
        verbose   = True,
        # Augmentation
        hsv_h     = 0.015,
        hsv_s     = 0.5,
        hsv_v     = 0.3,
        degrees   = 10.0,
        flipud    = 0.0,
        fliplr    = 0.5,
        mosaic    = 0.8,
        scale     = 0.4,
    )

    # Copy best weights
    best_pt = os.path.join(PROJECT_ROOT, "runs", "damage_pro", "weights", "best.pt")
    if os.path.exists(best_pt):
        dest = os.path.join(PROJECT_ROOT, "best.pt")
        shutil.copy2(best_pt, dest)
        print(f"\n✅ Best model saved to: {dest}")

    print("\n[Train] === Training Complete ===")
    return results


if __name__ == "__main__":
    dataset_path = download_dataset()
    if dataset_path:
        train_model(dataset_path)
    else:
        print("Dataset download failed. Please provide a dataset manually.")
