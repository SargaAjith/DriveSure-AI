from ultralytics import YOLO
import cv2
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predict_segmentation as engine

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(PROJECT_ROOT, "best.pt"))

# Test the EXACT image causing problems
TEST_IMAGE = os.path.join(PROJECT_ROOT, "0020.jpg")

print("="*60)
print("STEP 1: RAW YOLO at conf=0.01 (see everything)")
print("="*60)
img = cv2.imread(TEST_IMAGE)
if img is None:
    print("ERROR: Image not found. Place 0020.jpg in project")
    print("root as test_image.jpg and update TEST_IMAGE path")
    sys.exit(1)

h, w = img.shape[:2]
r = model(TEST_IMAGE, verbose=False,
          conf=0.01, iou=0.45, imgsz=640)[0]

print(f"Image size: {w}x{h}")
print(f"Total detections at conf=0.01: {len(r.boxes)}")
print()

if r.masks is not None:
    for i, (box, mask) in enumerate(
            zip(r.boxes, r.masks.xy)):
        conf = float(box.conf[0])
        pts = np.array(mask, dtype=np.int32)
        area = cv2.contourArea(pts)
        pct = (area / (h*w)) * 100
        x1,y1,x2,y2 = [int(v) for v in box.xyxy[0].tolist()]
        print(f"Detection {i+1}:")
        print(f"  conf     = {conf:.4f}")
        print(f"  area     = {area:.0f}px ({pct:.1f}% of image)")
        print(f"  bbox     = ({x1},{y1}) to ({x2},{y2})")
        print(f"  location = "
              f"{'TOP' if y1<h//3 else 'MID' if y1<2*h//3 else 'BOT'}-"
              f"{'LEFT' if x1<w//3 else 'MID' if x1<2*w//3 else 'RIGHT'}")
        print(f"  kept@0.75= {'YES' if conf>=0.75 else 'NO — filtered'}")
        print()
else:
    print("No masks at conf=0.01 — pure OpenCV problem")

print("="*60)
print("STEP 2: OpenCV breakdown")
print("="*60)
cv2_score = engine._opencv_damage_score(TEST_IMAGE)[0]
print(f"OpenCV final score: {cv2_score:.2f}")

print("="*60)
print("STEP 3: Full pipeline result")
print("="*60)
result = engine.predict(TEST_IMAGE)
print(f"damage_pct : {result['damage_pct']}")
print(f"severity   : {result['severity']}")
print(f"polygons   : {result['polygon_count']}")
print(f"source     : {result['source']}")
print(f"observation: {result['what_i_see']}")
