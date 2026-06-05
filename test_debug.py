from ultralytics import YOLO
import cv2
import numpy as np
import os
import glob
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

model = YOLO(os.path.join(PROJECT_ROOT, "best.pt"))

# ════════════════════════════════════════════════════
# TEST 1: RAW YOLO ON CLEAN CAR
# ════════════════════════════════════════════════════
TEST_IMAGE = "clean_car.jpg"

results = model(TEST_IMAGE, verbose=False,
                conf=0.01,   # very low — see EVERYTHING
                iou=0.45, imgsz=640, max_det=50)[0]

img = cv2.imread(TEST_IMAGE)
h, w = img.shape[:2]

print(f"\n{'='*60}")
print(f"IMAGE: {TEST_IMAGE}  size={w}x{h}")
print(f"TOTAL DETECTIONS AT conf=0.01: {len(results.boxes)}")
print(f"{'='*60}")

if results.masks is not None:
    for i, (box, mask) in enumerate(zip(results.boxes, results.masks.xy)):
        conf = float(box.conf[0])
        cls  = int(box.cls[0])
        pts  = np.array(mask, dtype=np.int32)
        area = cv2.contourArea(pts)
        pct  = (area / (h * w)) * 100

        # Draw on image for visual inspection
        color = (0, 255, 0) if conf < 0.50 else \
                (0, 165, 255) if conf < 0.75 else \
                (0, 0, 255)
        cv2.polylines(img, [pts], True, color, 2)
        cx = int(pts[:,0].mean()) if len(pts) > 0 else 0
        cy = int(pts[:,1].mean()) if len(pts) > 0 else 0
        cv2.putText(img, f"{conf:.2f}",
                    (cx, cy), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, color, 2)

        print(f"Detection {i+1}:")
        print(f"  conf  = {conf:.4f}")
        print(f"  class = {cls}")
        print(f"  area  = {area:.0f}px  ({pct:.1f}% of image)")
        print(f"  bbox  = {box.xyxy[0].tolist()}")
else:
    print("NO MASKS DETECTED at conf=0.01")

out_path = "debug_clean_car_detections.jpg"
cv2.imwrite(out_path, img)
print(f"\nDebug image saved: {out_path}")
print("GREEN  = conf < 0.50 (likely false positive)")
print("ORANGE = conf 0.50-0.75 (uncertain)")
print("RED    = conf > 0.75 (model is confident)")


# ════════════════════════════════════════════════════
# TEST 2: SAME TEST ON A DAMAGED CAR
# ════════════════════════════════════════════════════
TEST_IMAGE_DAMAGED = os.path.join("data", "images", "val", "Car damages 103.jpg")

results2 = model(TEST_IMAGE_DAMAGED, verbose=False,
                conf=0.01,
                iou=0.45, imgsz=640, max_det=50)[0]

img2 = cv2.imread(TEST_IMAGE_DAMAGED)
h2_img, w2_img = img2.shape[:2]

print(f"\n{'='*60}")
print(f"IMAGE: {TEST_IMAGE_DAMAGED}  size={w2_img}x{h2_img}")
print(f"TOTAL DETECTIONS AT conf=0.01: {len(results2.boxes)}")
print(f"{'='*60}")

if results2.masks is not None:
    for i, (box, mask) in enumerate(zip(results2.boxes, results2.masks.xy)):
        conf = float(box.conf[0])
        cls  = int(box.cls[0])
        pts  = np.array(mask, dtype=np.int32)
        area = cv2.contourArea(pts)
        pct  = (area / (h2_img * w2_img)) * 100

        color = (0, 255, 0) if conf < 0.50 else \
                (0, 165, 255) if conf < 0.75 else \
                (0, 0, 255)
        cv2.polylines(img2, [pts], True, color, 2)
        cx = int(pts[:,0].mean()) if len(pts) > 0 else 0
        cy = int(pts[:,1].mean()) if len(pts) > 0 else 0
        cv2.putText(img2, f"{conf:.2f}",
                    (cx, cy), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, color, 2)

        print(f"Detection {i+1}:")
        print(f"  conf  = {conf:.4f}")
        print(f"  class = {cls}")
        print(f"  area  = {area:.0f}px  ({pct:.1f}% of image)")
        print(f"  bbox  = {box.xyxy[0].tolist()}")
else:
    print("NO MASKS DETECTED at conf=0.01")

out_path2 = "debug_damaged_car_detections.jpg"
cv2.imwrite(out_path2, img2)
print(f"\nDebug image saved: {out_path2}")


# ════════════════════════════════════════════════════
# TEST 4: OPENCV SCORE ALONE ON CLEAN CAR
# ════════════════════════════════════════════════════
from predict_segmentation import _opencv_damage_score

cv2_score = _opencv_damage_score(TEST_IMAGE)[0]
print(f"\n{'='*60}")
print(f"OpenCV score on clean car: {cv2_score:.2f}")
print(f"Expected: < 5.0 for clean car")
if cv2_score > 10:
    print("WARNING: OpenCV over-scoring clean car")
    print("Problem is in _opencv_damage_score formula")
else:
    print("OpenCV score OK — problem is in YOLO detection")


# ════════════════════════════════════════════════════
# TEST 5: CONFIDENCE DISTRIBUTION ACROSS 10 IMAGES
# ════════════════════════════════════════════════════
image_files = glob.glob("**/*.jpg", recursive=True) + \
              glob.glob("**/*.jpeg", recursive=True) + \
              glob.glob("**/*.png", recursive=True)

# Filter out our newly created debug images
image_files = [f for f in image_files if "debug" not in f][:10]

print(f"\n{'='*60}")
print("CONFIDENCE SCAN ACROSS ALL TEST IMAGES")
print(f"{'='*60}")
print(f"{'Image':<30} {'Detections':>10} "
      f"{'MaxConf':>8} {'Coverage':>10}")
print("-" * 60)

for img_path in image_files:
    try:
        r = model(img_path, verbose=False,
                  conf=0.01, imgsz=640)[0]
        n_det = len(r.boxes)
        if n_det > 0:
            max_conf = float(r.boxes.conf.max())
            if r.masks is not None:
                img_cv = cv2.imread(img_path)
                if img_cv is not None:
                    h2, w2 = img_cv.shape[:2]
                    total_area = 0
                    for mask in r.masks.xy:
                        pts2 = np.array(mask, dtype=np.int32)
                        total_area += cv2.contourArea(pts2)
                    coverage = (total_area/(h2*w2))*100
                else:
                    coverage = 0.0
            else:
                coverage = 0.0
        else:
            max_conf = 0.0
            coverage = 0.0

        name = os.path.basename(img_path)[:28]
        print(f"{name:<30} {n_det:>10} "
              f"{max_conf:>8.3f} {coverage:>9.1f}%")
    except Exception as e:
        print(f"{img_path:<30} ERROR: {e}")

print(f"{'='*60}")
print("\nLook for:")
print("  Clean cars with high MaxConf → model misclassifying")
print("  Clean cars with high Coverage → formula inflating")
print("  If all images show similar conf → threshold issue")
