"""
prepare_dataset_v2.py
=====================
Improved dataset preparation from masks_human side-by-side images.
Uses higher difference threshold + morphological erosion to create
tighter, more accurate damage masks.
"""

import os
import sys
import random
import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ─── Config ──────────────────────────────────────────────────────────────────
SRC_DIR      = r"C:\Users\nsti-\Downloads\Ashima\CAPSTONE\car_parts_dataset\Car damages dataset\File1\masks_human"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data_v2")
TRAIN_SPLIT  = 0.8
DIFF_THRESH  = 80          # Higher threshold = tighter masks
MIN_AREA     = 200         # Minimum contour area in pixels
ERODE_KERNEL = 5           # Erosion kernel size to shrink mask edges
SEED         = 42


def extract_mask_tight(img_path):
    """
    Extract tight damage mask from a side-by-side image.
    Left = original, Right = overlay annotation.
    Uses higher threshold + erosion for tighter masks.
    """
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    w, h = img.size
    mid = w // 2

    left  = arr[:, :mid].astype(np.float32)
    right = arr[:, mid:mid+mid].astype(np.float32)

    # Per-channel difference
    diff = np.abs(left - right)
    diff_mag = diff.sum(axis=2)  # Sum across RGB channels

    # Binary mask with higher threshold
    binary = (diff_mag > DIFF_THRESH).astype(np.uint8) * 255

    if not CV2_AVAILABLE:
        return binary, mid, arr.shape[0]

    # Morphological cleanup: erode to shrink, then small dilation to smooth
    kernel_erode  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ERODE_KERNEL, ERODE_KERNEL))
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    # Close small gaps first, then erode to tighten
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_dilate, iterations=1)
    binary = cv2.erode(binary, kernel_erode, iterations=2)
    # Small dilate to smooth jagged edges
    binary = cv2.dilate(binary, kernel_dilate, iterations=1)

    return binary, mid, arr.shape[0]


def mask_to_yolo_polygons(binary_mask, img_w, img_h, class_id=0):
    """Convert binary mask to YOLO segmentation format polygons."""
    if not CV2_AVAILABLE:
        return []

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lines = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue

        # Simplify contour to reduce point count
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) < 3:
            continue

        # Normalize coordinates
        points = []
        for pt in approx:
            x_norm = pt[0][0] / img_w
            y_norm = pt[0][1] / img_h
            x_norm = max(0.0, min(1.0, x_norm))
            y_norm = max(0.0, min(1.0, y_norm))
            points.extend([f"{x_norm:.6f}", f"{y_norm:.6f}"])

        if len(points) >= 6:  # At least 3 points
            line = f"{class_id} " + " ".join(points)
            lines.append(line)

    return lines


def main():
    print("=" * 60)
    print("  Dataset Preparation v2 — Tighter Masks")
    print("=" * 60)

    if not os.path.exists(SRC_DIR):
        print(f"ERROR: Source directory not found: {SRC_DIR}")
        sys.exit(1)

    if not CV2_AVAILABLE:
        print("ERROR: OpenCV required. Install: pip install opencv-python-headless")
        sys.exit(1)

    # Create directories
    for split in ["train", "val"]:
        os.makedirs(os.path.join(DATA_DIR, "images", split), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, "labels", split), exist_ok=True)

    # Get all source PNGs
    src_files = sorted([f for f in os.listdir(SRC_DIR) if f.endswith(".png")])
    print(f"\nFound {len(src_files)} source images")

    random.seed(SEED)
    random.shuffle(src_files)
    split_idx = int(len(src_files) * TRAIN_SPLIT)
    train_files = src_files[:split_idx]
    val_files   = src_files[split_idx:]

    print(f"Train: {len(train_files)}, Val: {len(val_files)}")
    print(f"Config: threshold={DIFF_THRESH}, erode_kernel={ERODE_KERNEL}, min_area={MIN_AREA}")

    stats = {"processed": 0, "skipped": 0, "total_masks": 0}

    for split_name, file_list in [("train", train_files), ("val", val_files)]:
        for fname in file_list:
            src_path = os.path.join(SRC_DIR, fname)
            base     = os.path.splitext(fname)[0]

            try:
                binary, img_w, img_h = extract_mask_tight(src_path)
                yolo_lines = mask_to_yolo_polygons(binary, img_w, img_h)

                if not yolo_lines:
                    stats["skipped"] += 1
                    continue

                # Save the LEFT half (original image) as training image
                pil_img = Image.open(src_path).convert("RGB")
                arr = np.array(pil_img)
                left_img = Image.fromarray(arr[:, :img_w])

                img_out = os.path.join(DATA_DIR, "images", split_name, f"{base}.jpg")
                lbl_out = os.path.join(DATA_DIR, "labels", split_name, f"{base}.txt")

                left_img.save(img_out, "JPEG", quality=95)
                with open(lbl_out, "w") as f:
                    f.write("\n".join(yolo_lines) + "\n")

                stats["processed"] += 1
                stats["total_masks"] += len(yolo_lines)

            except Exception as e:
                print(f"  WARN: {fname}: {e}")
                stats["skipped"] += 1

    print(f"\n{'='*60}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Skipped:   {stats['skipped']}")
    print(f"  Total mask regions: {stats['total_masks']}")
    print(f"  Output: {DATA_DIR}")

    # Verify mask quality
    print(f"\nMask area statistics:")
    label_dir = os.path.join(DATA_DIR, "labels", "train")
    areas = []
    for f in os.listdir(label_dir)[:50]:
        path = os.path.join(label_dir, f)
        with open(path) as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) < 7:
                    continue
                coords = [float(x) for x in parts[1:]]
                xs = coords[0::2]
                ys = coords[1::2]
                n = len(xs)
                area = 0
                for i in range(n):
                    j = (i + 1) % n
                    area += xs[i] * ys[j]
                    area -= xs[j] * ys[i]
                area = abs(area) / 2.0
                areas.append(area * 100)

    if areas:
        areas = np.array(areas)
        print(f"  Mean:   {areas.mean():.1f}%")
        print(f"  Median: {np.median(areas):.1f}%")
        print(f"  Min:    {areas.min():.1f}%")
        print(f"  Max:    {areas.max():.1f}%")

    # Write dataset.yaml
    yaml_path = os.path.join(PROJECT_ROOT, "dataset_v2.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"path: {DATA_DIR}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        f.write("  0: damage\n")

    print(f"\n  dataset_v2.yaml: {yaml_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
