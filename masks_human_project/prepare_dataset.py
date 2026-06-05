"""
prepare_dataset.py
==================
Extracts binary damage masks from the `masks_human` side-by-side PNG dataset,
converts damage regions to normalized YOLO segmentation polygon labels, and
splits data into 80% train / 20% validation sets.

Dataset format in masks_human:
  Each PNG (width ~1275, height ~419) has:
    - Left half  : original car image (width = img_width)
    - Right half : human-annotated damage overlay (starts at offset = img_width + 1)
  The damage regions appear as colored overlays (differ from the original pixels).

Output structure:
  masks_human_project/
    data/
      images/
        train/  (80%)
        val/    (20%)
      labels/
        train/  (YOLO polygon .txt files)
        val/
    dataset.yaml
"""

import os
import shutil
import random
import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[Warning] opencv-python not installed. Using PIL-based contour fallback.")

# ─── Configuration ────────────────────────────────────────────────────────────
MASKS_HUMAN_DIR = r"C:\Users\nsti-\Downloads\Ashima\CAPSTONE\car_parts_dataset\Car damages dataset\File1\masks_human"
IMG_DIR         = r"C:\Users\nsti-\Downloads\Ashima\CAPSTONE\car_parts_dataset\Car damages dataset\File1\img"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")

TRAIN_IMAGES = os.path.join(DATA_DIR, "images", "train")
VAL_IMAGES   = os.path.join(DATA_DIR, "images", "val")
TRAIN_LABELS = os.path.join(DATA_DIR, "labels", "train")
VAL_LABELS   = os.path.join(DATA_DIR, "labels", "val")

DIFF_THRESHOLD   = 25     # Absolute pixel diff to detect overlay
MIN_CONTOUR_AREA = 200    # Minimum contour area (pixels²) to keep
TRAIN_SPLIT      = 0.80
CLASS_ID         = 0      # Single class: "Vehicle Damage"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ─── Directory setup ──────────────────────────────────────────────────────────
for d in [TRAIN_IMAGES, VAL_IMAGES, TRAIN_LABELS, VAL_LABELS]:
    os.makedirs(d, exist_ok=True)

# ─── Helper: extract binary mask from side-by-side PNG ────────────────────────
def extract_damage_mask(mask_path: str):
    """
    Given a side-by-side masks_human PNG, extracts a binary damage mask.
    Returns (original_image_np, binary_mask_np) where binary_mask is uint8 0/255.
    """
    img = Image.open(mask_path).convert("RGB")
    arr = np.array(img)
    full_h, full_w, _ = arr.shape

    # The left half is the original image
    orig_w = full_w // 2
    left  = arr[:, :orig_w, :].astype(np.float32)
    # Right half starts at orig_w + 1 (1-pixel alignment offset confirmed by analysis)
    right = arr[:, orig_w + 1 : orig_w + 1 + orig_w, :].astype(np.float32)

    # Handle edge case where right slice is slightly narrower
    min_w = min(left.shape[1], right.shape[1])
    left  = left[:, :min_w, :]
    right = right[:, :min_w, :]

    # Absolute pixel-wise difference
    diff = np.abs(left - right)
    diff_sum = np.sum(diff, axis=2)  # Sum across RGB channels

    binary_mask = np.zeros((full_h, min_w), dtype=np.uint8)
    binary_mask[diff_sum > DIFF_THRESHOLD] = 255

    original_np = left.astype(np.uint8)
    return original_np, binary_mask

# ─── Helper: extract YOLO polygon points from binary mask ─────────────────────
def mask_to_yolo_polygons(binary_mask: np.ndarray, img_h: int, img_w: int):
    """
    Given a binary mask (0/255), finds contours and converts to YOLO polygon format.
    Returns a list of polygon strings: ["<class_id> x1 y1 x2 y2 ...", ...]
    """
    polygons = []

    if CV2_AVAILABLE:
        # Morphological cleanup to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        clean_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_OPEN,  kernel)

        contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_CONTOUR_AREA:
                continue
            # Approximate to reduce polygon complexity
            epsilon = 0.005 * cv2.arcLength(cnt, True)
            approx  = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) < 3:
                continue

            pts = approx.reshape(-1, 2)
            # Normalize to [0, 1]
            normalized = []
            for x, y in pts:
                nx = float(x) / img_w
                ny = float(y) / img_h
                nx = max(0.0, min(1.0, nx))
                ny = max(0.0, min(1.0, ny))
                normalized.extend([f"{nx:.6f}", f"{ny:.6f}"])

            if len(normalized) >= 6:  # at least 3 points
                polygons.append(f"{CLASS_ID} " + " ".join(normalized))
    else:
        # Fallback: bounding-box style polygon from mask extents
        rows = np.any(binary_mask > 0, axis=1)
        cols = np.any(binary_mask > 0, axis=0)
        if not rows.any():
            return []
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        # Convert to normalized bbox corners as polygon
        x1 = cmin / img_w; y1 = rmin / img_h
        x2 = cmax / img_w; y2 = rmax / img_h
        polygons.append(
            f"{CLASS_ID} {x1:.6f} {y1:.6f} {x2:.6f} {y1:.6f} "
            f"{x2:.6f} {y2:.6f} {x1:.6f} {y2:.6f}"
        )

    return polygons

# ─── Main pipeline ────────────────────────────────────────────────────────────
def prepare_dataset():
    mask_files = sorted([f for f in os.listdir(MASKS_HUMAN_DIR) if f.lower().endswith(".png")])
    print(f"[Prepare] Found {len(mask_files)} mask files.")

    valid_items = []
    skipped = 0

    for idx, fname in enumerate(mask_files):
        mask_path = os.path.join(MASKS_HUMAN_DIR, fname)
        try:
            orig_np, binary_mask = extract_damage_mask(mask_path)
            img_h, img_w = orig_np.shape[:2]

            # Skip if mask has too little damage
            damage_ratio = np.sum(binary_mask > 0) / (img_h * img_w)
            if damage_ratio < 0.005:
                skipped += 1
                continue

            polygons = mask_to_yolo_polygons(binary_mask, img_h, img_w)
            if not polygons:
                skipped += 1
                continue

            valid_items.append({
                "fname":    fname,
                "orig_np":  orig_np,
                "polygons": polygons
            })

            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(mask_files)} ...")

        except Exception as e:
            print(f"  [Skip] {fname}: {e}")
            skipped += 1

    print(f"\n[Prepare] Valid samples: {len(valid_items)}, Skipped: {skipped}")

    # Shuffle and split
    random.shuffle(valid_items)
    split_idx = int(len(valid_items) * TRAIN_SPLIT)
    train_items = valid_items[:split_idx]
    val_items   = valid_items[split_idx:]

    def save_items(items, img_dir, lbl_dir, subset_name):
        saved = 0
        for item in items:
            stem = os.path.splitext(item["fname"])[0]
            img_out  = os.path.join(img_dir, f"{stem}.jpg")
            lbl_out  = os.path.join(lbl_dir, f"{stem}.txt")

            # Save original image as JPEG
            pil_img = Image.fromarray(item["orig_np"])
            pil_img = pil_img.resize((640, 640), Image.LANCZOS)
            pil_img.save(img_out, "JPEG", quality=95)

            # Save YOLO polygon label
            # Rescale contour coords since we resized to 640x640
            # Polygon coords are already normalized, so they remain valid
            with open(lbl_out, "w") as f:
                f.write("\n".join(item["polygons"]))

            saved += 1
        print(f"  [{subset_name}] Saved {saved} samples.")

    print(f"\n[Prepare] Saving train set ({len(train_items)} items)...")
    save_items(train_items, TRAIN_IMAGES, TRAIN_LABELS, "Train")

    print(f"[Prepare] Saving val set ({len(val_items)} items)...")
    save_items(val_items, VAL_IMAGES, VAL_LABELS, "Val")

    # Write dataset.yaml
    yaml_path = os.path.join(PROJECT_ROOT, "dataset.yaml")
    yaml_content = f"""# YOLOv8 Segmentation Dataset Configuration
# Auto-generated by prepare_dataset.py

path: {DATA_DIR.replace(os.sep, "/")}
train: images/train
val:   images/val

nc: 1
names:
  0: Vehicle Damage
"""
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"\n[Prepare] dataset.yaml written to: {yaml_path}")
    print(f"[Prepare] === Dataset Preparation Complete ===")
    print(f"  Train: {len(train_items)} | Val: {len(val_items)} | Skipped: {skipped}")


if __name__ == "__main__":
    prepare_dataset()
