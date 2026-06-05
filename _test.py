"""Test hybrid YOLO+OpenCV detection."""
import sys, os
sys.path.insert(0, "masks_human_project")
import predict_segmentation as engine

val_dir = "masks_human_project/data/images/val"
imgs = sorted([f for f in os.listdir(val_dir) if f.endswith(('.jpg','.png'))])

print("Hybrid YOLO+OpenCV detection results:")
print("-" * 85)
for name in imgs[:15]:
    r = engine.predict(os.path.join(val_dir, name))
    print(f"{name[:30]:30s} | {r['source']:10s} | {r['severity']:9s} | "
          f"Dmg: {r['damage_pct']:5.1f}% | Zones: {r['polygon_count']:2d} | Conf: {r['confidence']:.2f}")
print("-" * 85)
